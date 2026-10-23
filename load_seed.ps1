$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
function Run($cmd) {
    Write-Host ">> $cmd" -ForegroundColor Cyan
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED at: $cmd" -ForegroundColor Red; Write-Host "Stop here and send this screen to Aliyah." -ForegroundColor Red; exit 1 }
}
Run "git checkout one-app"
Run "git pull origin one-app"
Run "python manage.py migrate"
Run "python manage.py loaddata seed_data/part_caudan_destination.json"
Run "python manage.py loaddata seed_data/part_food_cards.json"
Run "python manage.py loaddata seed_data/part_food_spots.json"
Run "python manage.py loaddata seed_data/part_caudan_event.json"
Write-Host "ALL DONE - now run: python manage.py runserver" -ForegroundColor Green
