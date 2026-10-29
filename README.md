Mauritius Explore
Web and Mobile Applications Development (ICT 2207Y(3)), University of Mauritius
Team: Web Wizards
Repository: https://github.com/ghanishachothi/Website_Mauritius_Explore
Team members:
- Ghanisha Chothi (2517659)
- Nusaibah Banu Khodabocus (2517669)
- Aliyah Fateemah Cadersa (2516986)
- Sabah Bibi Dulloo (2516802)
- Suwaibah Radim (2517367)
- Mithili Khushi Laxshmi Vandevi Jhurree (2516982)
How to run the project
You need Python 3.12 or newer. The final code is on the main branch.
Open a terminal in VS Code (PowerShell) and run:
git clone https://github.com/ghanishachothi/Website_Mauritius_Explore.git
cd Website_Mauritius_Explore
git checkout main
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Next, copy the .env file we submitted into the project folder, next to manage.py. It connects the site to our shared
database and photos, so without it the website will be empty. If Windows renamed it to env.txt, rename it back
with:
Rename-Item env.txt .env
Then start the website:
python manage.py migrate
python manage.py runserver
and open http://127.0.0.1:8000/ in your browser.
Admin login
Go to http://127.0.0.1:8000/admin/
Username: Anwar_C
Password: lavabo123
Presentation
The slides are in Mauritius_Explore_Presentation_final.pptx. Please open them with Microsoft PowerPoint.
