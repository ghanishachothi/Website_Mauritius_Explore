"""
finish_merge.py  -  AFTER the .py files of apps/explore are in place, this does the rest: puts the 6 Django apps (core, users, destinations, experiences,
bookings, admin_dashboard) into ONE normal Django app called  apps/explore  with
ONE models.py, ONE views.py, ONE urls.py, ONE admin.py, ONE forms.py, ONE tests.py,
signals.py, context_processors.py, management/commands, templates/ and static/.

Run it ONCE, from the project root (the folder with manage.py), on a Git branch:
    python finish_merge.py

It does NOT delete the old apps (it only copies). It stops if apps/explore exists.
Template folders, static folders and URL namespaces keep their names, so the pages
and {% url 'core:home' %} style links do not change.
"""
import ast
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
APPS = ROOT / 'apps'
NEW = APPS / 'explore'
OLD = ['core', 'users', 'destinations', 'experiences', 'bookings', 'admin_dashboard']
OLD_RE = '|'.join(OLD)
MODEL_APPS = ['core', 'users', 'destinations', 'experiences', 'bookings']
problems = []

# functions that exist under the same name in two apps -> rename one of them
RENAMES = {
    ('views', 'destinations'): ['explore_your_way', 'reserve_experience'],
}


def read(path):
    return Path(path).read_text(encoding='utf-8-sig')


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


# --------------------------------------------------------------------------- helpers
def fix_imports(text):
    """Imports that pointed at another app now point at the same app."""
    text = re.sub(r'from apps\.(?:%s)\.models import' % OLD_RE, 'from .models import', text)
    text = re.sub(r'from apps\.(?:%s)\.forms import' % OLD_RE, 'from .forms import', text)
    text = re.sub(r'from apps\.(?:%s) import views\b' % OLD_RE, 'from . import views', text)
    text = re.sub(r'from apps\.(?:%s)\.views import' % OLD_RE, 'from .views import', text)
    text = re.sub(r'from apps\.core\.context_processors', 'from .context_processors', text)
    return text


def fix_model_strings(text):
    """'destinations.Guide' -> 'explore.Guide' (foreign-key strings in models.py)."""
    return re.sub(r"""(['"])(?:%s)\.([A-Za-z]+)\1""" % '|'.join(MODEL_APPS),
                  r'\1explore.\2\1', text)


def fix_admin_urls(text):
    """{% url 'admin:destinations_guide_add' %} -> admin:explore_guide_add"""
    text = text.replace('admin:destinations_review_', 'admin:explore_guidereview_')
    return re.sub(r"admin:(?:%s)_([a-z]+)_(add|change|changelist|delete|history)" % '|'.join(MODEL_APPS),
                  r'admin:explore_\1_\2', text)


def rename_symbol(text, old, new):
    """Rename a function and every use of it (not strings, not attributes)."""
    tree = ast.parse(text)
    lines = text.split('\n')
    edits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == old:
            line = lines[node.lineno - 1]
            col = line.index('def ') + 4
            edits.append((node.lineno - 1, col))
        elif isinstance(node, ast.Name) and node.id == old:
            edits.append((node.lineno - 1, node.col_offset))
    for ln, col in sorted(edits, reverse=True):
        lines[ln] = lines[ln][:col] + new + lines[ln][col + len(old):]
    return '\n'.join(lines)


def split_imports(text):
    """Return (list of import statements, the rest of the file without them)."""
    tree = ast.parse(text)
    lines = text.split('\n')
    imports, drop = [], set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            seg = '\n'.join(lines[node.lineno - 1: node.end_lineno])
            imports.append(seg)
            drop.update(range(node.lineno - 1, node.end_lineno))
    rest = '\n'.join(l for i, l in enumerate(lines) if i not in drop)
    return imports, rest.strip('\n')


def join_files(kind, pieces):
    """pieces = [(app, source text)] -> one file: imports on top, then each app's code."""
    all_imports, seen, bodies = [], set(), []
    for app, text in pieces:
        imports, rest = split_imports(text)
        for imp in imports:
            key = re.sub(r'\s+', ' ', imp)
            if key not in seen:
                seen.add(key)
                all_imports.append(imp)
        if rest.strip():
            bodies.append('# ' + '=' * 70 + '\n# from the old "%s" app\n# ' % app + '=' * 70 + '\n\n' + rest)
    future = [i for i in all_imports if i.startswith('from __future__')]
    others = [i for i in all_imports if not i.startswith('from __future__')]
    return '\n'.join(future + others) + '\n\n\n' + '\n\n\n'.join(bodies) + '\n'


def copy_tree_merge(src, dst):
    if not src.exists():
        return
    for f in src.rglob('*'):
        if f.is_dir() or '__pycache__' in f.parts:
            continue
        target = dst / f.relative_to(src)
        if target.exists():
            if target.read_bytes() != f.read_bytes():
                problems.append('CLASH (kept the first one): %s' % target.relative_to(ROOT))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)


def has_content(path):
    if not path.exists():
        return False
    tree = ast.parse(read(path))
    return any(not isinstance(n, (ast.Import, ast.ImportFrom)) and
               not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)) for n in tree.body)


# --------------------------------------------------------------------------- main
def main():
    if not (ROOT / 'manage.py').exists() or not APPS.exists():
        sys.exit('Run this from the project root (the folder with manage.py).')

    if not NEW.exists():
        sys.exit('apps/explore does not exist yet. Place the .py files from explore_code.zip first.')
    for needed in ('models.py', 'views.py', 'urls.py', 'admin.py', 'forms.py', 'apps.py'):
        if not (NEW / needed).exists():
            sys.exit('apps/explore/%s is missing. Place all the files from explore_code.zip first.' % needed)

    # ------------------------------------------------ templates / static / fixtures
    for app in OLD:
        copy_tree_merge(APPS / app / 'templates', NEW / 'templates')
        copy_tree_merge(APPS / app / 'static', NEW / 'static')
        copy_tree_merge(APPS / app / 'fixtures', NEW / 'fixtures')
    for folder in (NEW / 'templates', ROOT / 'templates'):
        for html in folder.rglob('*.html'):
            text = html.read_text(encoding='utf-8-sig')
            new = fix_admin_urls(text)
            if new != text:
                html.write_text(new, encoding='utf-8', newline='\n')

    # ------------------------------------------------ project files
    settings = ROOT / 'mauritius_explore' / 'settings.py'
    s = read(settings)
    s = re.sub(r"(\s*)'apps\.core',\n\s*'apps\.users',\n\s*'apps\.destinations',\n\s*'apps\.experiences',\n"
               r"\s*'apps\.bookings',\n\s*'apps\.admin_dashboard',",
               r"\1'apps.explore',", s)
    s = s.replace("'apps.core.context_processors.site_nav'", "'apps.explore.context_processors.site_nav'")
    if "'apps.explore'," not in s:
        problems.append('mauritius_explore/settings.py: INSTALLED_APPS was not changed automatically - tell Claude.')
    write(settings, s)

    rooturls = ROOT / 'mauritius_explore' / 'urls.py'
    r = read(rooturls)
    r = re.sub(r'from apps\.destinations import views as destination_views',
               'from apps.explore import urls as explore_urls\nfrom apps.explore import views as destination_views', r)
    r = re.sub(r'destination_views\.(explore_your_way|reserve_experience)\b',
               r'destination_views.destinations_\1', r)
    r = re.sub(r"include\('apps\.(%s)\.urls'\)" % OLD_RE,
               r"include((explore_urls.\1_patterns, '\1'))", r)
    write(rooturls, r)

    for f in ROOT.glob('*.py'):          # helper scripts in the project root
        if f.name == Path(__file__).name:
            continue
        text = f.read_text(encoding='utf-8-sig')
        new = re.sub(r'from apps\.(?:%s)\.models import' % '|'.join(MODEL_APPS), 'from apps.explore.models import', text)
        new = re.sub(r'apps\.get_model\((["\'])(?:%s)\1\s*,' % '|'.join(MODEL_APPS), r'apps.get_model(\1explore\1,', new)
        if new != text:
            write(f, new)

    # ------------------------------------------------ JSON model names
    def relabel(label):
        app, _, model = label.partition('.')
        if app in MODEL_APPS:
            if label.lower() == 'destinations.review':
                return 'explore.guidereview'
            return 'explore.' + model.lower()
        return label

    backup = ROOT / 'seed_data' / '_before_one_app'
    backup.mkdir(exist_ok=True)
    json_files = sorted((ROOT / 'seed_data').glob('*.json')) + sorted((NEW / 'fixtures').glob('*.json'))
    for js in json_files:
        data = json.loads(js.read_text(encoding='utf-8-sig'))
        shutil.copy2(js, backup / js.name)
        for obj in data:
            obj['model'] = relabel(obj['model'])
        js.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8', newline='\n')

    merge = ROOT / 'seed_data' / 'merge_seed.py'
    if merge.exists():
        m = read(merge)
        m = m.replace(
            "EXCLUDES = ['auth', 'contenttypes', 'admin', 'sessions', 'bookings', 'users',\n"
            "            'experiences.chatsession', 'experiences.chatmessage',\n"
            "            'experiences.favourite', 'experiences.review']\n"
            "SKIP_MODELS = set(EXCLUDES[6:])",
            "EXCLUDES = ['auth', 'contenttypes', 'admin', 'sessions',\n"
            "            'explore.booking', 'explore.payment', 'explore.profile',\n"
            "            'explore.chatsession', 'explore.chatmessage',\n"
            "            'explore.favourite', 'explore.review']\n"
            "SKIP_MODELS = {e for e in EXCLUDES if '.' in e}")
        m = m.replace(
            "FILE_SKIP_PREFIX = {'suwaibah.json': ('core.',)}",
            "FILE_SKIP_PREFIX = {'suwaibah.json': ('explore.sitepage', 'explore.footercolumn',\n"
            "                                      'explore.footerlink', 'explore.applink',\n"
            "                                      'explore.sociallink', 'explore.monthtip',\n"
            "                                      'explore.contactmessage', 'explore.appwaitlist')}")
        if "'explore.booking'" not in m or "'explore.sitepage'" not in m:
            problems.append('seed_data/merge_seed.py was not updated automatically - tell Claude.')
        write(merge, m)

    # ------------------------------------------------ check what we wrote
    for f in NEW.rglob('*.py'):
        if 'migrations' in f.parts:
            continue
        try:
            ast.parse(f.read_text(encoding='utf-8'))
        except SyntaxError as exc:
            problems.append('%s has a syntax problem at line %s' % (f.relative_to(ROOT), exc.lineno))
        for n, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            if re.search(r'apps\.(%s)\b' % OLD_RE, line) and not line.strip().startswith('#') and '"""' not in line:
                problems.append('%s:%d still mentions an old app: %s' % (f.relative_to(ROOT), n, line.strip()))

    print('Done. New app: apps/explore  (models.py, views.py, urls.py, admin.py, forms.py, tests.py ...)')
    if problems:
        print('\nPROBLEMS (copy this to Claude):')
        for p in problems:
            print('  -', p)
    else:
        print('No problems found.')


main()
