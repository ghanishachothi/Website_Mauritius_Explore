import os, sys, mimetypes, pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mauritius_explore.settings')
import django
django.setup()
import boto3
from botocore.config import Config
from django.conf import settings
apply = '--apply' in sys.argv
for k in ('SUPABASE_S3_KEY', 'SUPABASE_S3_SECRET', 'SUPABASE_S3_ENDPOINT', 'SUPABASE_BUCKET'):
    if not os.environ.get(k):
        sys.exit('Missing in .env: ' + k)
root = pathlib.Path(settings.MEDIA_ROOT)
if not root.exists():
    sys.exit('No media folder at ' + str(root))
cfg = Config(retries={'max_attempts': 8, 'mode': 'standard'}, connect_timeout=30, read_timeout=120, max_pool_connections=12)
s3 = boto3.client('s3', endpoint_url=os.environ['SUPABASE_S3_ENDPOINT'],
                  aws_access_key_id=os.environ['SUPABASE_S3_KEY'],
                  aws_secret_access_key=os.environ['SUPABASE_S3_SECRET'],
                  region_name=os.environ.get('SUPABASE_S3_REGION', 'us-east-1'), config=cfg)
bucket = os.environ['SUPABASE_BUCKET']
existing = set()
for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket):
    for o in page.get('Contents', []):
        existing.add(o['Key'])
files = [p for p in root.rglob('*') if p.is_file()]
todo = [p for p in files if p.relative_to(root).as_posix() not in existing]
print('Files in media folder:', len(files), '| already in Supabase:', len(files) - len(todo), '| to upload:', len(todo), flush=True)
if not apply:
    print('PREVIEW ONLY. Run again with --apply to upload.')
    sys.exit(0)
def up(p):
    key = p.relative_to(root).as_posix()
    ctype = mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
    s3.upload_file(str(p), bucket, key, ExtraArgs={'ContentType': ctype})
    return key
done = 0
failed = []
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(up, p): p for p in todo}
    for f in as_completed(futs):
        try:
            f.result()
            done += 1
        except Exception as e:
            failed.append(futs[f].name)
        n = done + len(failed)
        if n % 10 == 0:
            print(n, '/', len(todo), 'done,', len(failed), 'failed', flush=True)
print('Uploaded', done, 'of', len(todo), '| failed:', len(failed))
for name in failed[:10]:
    print('FAILED', name)
