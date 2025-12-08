coverage:
	coverage run --source='.' manage.py test
	coverage html
	xdg-open htmlcov/index.html

test:
	python manage.py test

complexity:
	radon cc -a -s . > complexity_report.txt
	xenon --max-absolute B --max-modules B --max-average B . > xenon_report.txt
	cat complexity_report.txt
	cat xenon_report.txt

check-style:
	flake8 --exit-zero
	autopep8 --diff --recursive --aggressive --aggressive .
	isort --check-only .

fix-style:
	autopep8 --in-place --recursive --aggressive --aggressive .
	isort .

activate:
	python3 -m venv .venv
	source .venv/bin/activate

install:
	pip3 install -r requirements.txt

run:
	pip3 install -r requirements.txt
	python3 manage.py makemigrations
	python3 manage.py migrate
	python3 manage.py runserver 0.0.0.0:8001

shell:
	python3 manage.py shell_plus --ipython

freeze:
	pip freeze > requirements.txt

deploy:
	git pull origin staging
	make install
	make migrate
	make collectstatic
	sudo systemctl restart gunicorn
	sudo systemctl restart nginx