@echo off

REM Jalankan 5 bot dalam jendela terpisah
start "" python main.py --email bot1@student.itera.ac.id --password 123456 --name CBot1 --team etimo
start "" python main.py --email bot2@student.itera.ac.id --password 123456 --name CBot2 --team etimo
start "" python main.py --email bot3@student.itera.ac.id --password 123456 --name CBot3 --team etimo
start "" python main.py --email bot4@student.itera.ac.id --password 123456 --name CBot4 --team etimo
start "" python main.py --email bot5@student.itera.ac.id --password 123456 --name CBot5 --team etimo