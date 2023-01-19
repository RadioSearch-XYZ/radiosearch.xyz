# Just some boilerplates for setting this thing up

python-installs:
	bash ./build/pipinst.sh
build:
	bash ./build/compile.sh
db:
	python3 -c 'from app import app, db;app.app_context().push();db.create_all()'

clean:
	rm -rfv  __pycache__ build *.spec

reset:
	python3 -c 'from app import app, db, Radio;app.app_context().push();db.session.delete(Radio.query.all());db.session.commit();exit(0)'

install:
	make python-installs
	make db