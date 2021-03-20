PYTHON ?= python
CURL   ?= curl
VENV   ?= venv
WGET   ?= wget --no-check-certificate

LADDER_MAP_PACK_VERSION = 2020-12-28
LADDER_MAP_PACK = ladderweb/static/ladder-map-pack-$(LADDER_MAP_PACK_VERSION).zip

RAGL_MAP_PACK_VERSION = 2020-12-28
RAGL_MAP_PACK = raglweb/static/ragl-map-pack-$(RAGL_MAP_PACK_VERSION).zip

LADDER_STATIC = ladderweb/static/Chart.min.css ladderweb/static/Chart.bundle.min.js $(LADDER_MAP_PACK)

# https://github.com/chartjs/Chart.js/releases/latest
CHART_JS_VERSION = 2.9.3

ladderdev: initladderdev
	FLASK_APP=ladderweb FLASK_ENV=development FLASK_RUN_PORT=5000 $(VENV)/bin/flask run

initladderdev: $(VENV) $(LADDER_STATIC) instance/db.sqlite3 instance/db-1m.sqlite3

ladderweb/static/Chart.min.css:
	$(CURL) -L https://cdnjs.cloudflare.com/ajax/libs/Chart.js/$(CHART_JS_VERSION)/Chart.min.css -o $@

ladderweb/static/Chart.bundle.min.js:
	$(CURL) -L https://cdnjs.cloudflare.com/ajax/libs/Chart.js/$(CHART_JS_VERSION)/Chart.bundle.min.js -o $@

instance/db.sqlite3: instance
	$(VENV)/bin/ora-ladder -d $@

instance/db-1m.sqlite3: instance
	$(VENV)/bin/ora-ladder -d $@

ragldev: initragldev
	FLASK_APP=raglweb FLASK_ENV=development FLASK_RUN_PORT=5001 $(VENV)/bin/flask run

initragldev: $(VENV) $(RAGL_MAP_PACK) instance/db-ragl.sqlite3

instance/db-ragl.sqlite3: instance
	$(VENV)/bin/ora-ragl -d $@

instance:
	mkdir -p $@

wheel: $(VENV)
	$(VENV)/bin/python -m pip install wheel && python setup.py bdist_wheel

mappacks: $(LADDER_MAP_PACK) $(RAGL_MAP_PACK)

$(LADDER_MAP_PACK): $(VENV)
	$(VENV)/bin/ora-mapstool misc/map-pools/ladder.maps --pack $(LADDER_MAP_PACK)

$(RAGL_MAP_PACK): $(VENV)
	$(VENV)/bin/ora-mapstool misc/map-pools/ragl-s10.maps --pack $(RAGL_MAP_PACK)

test: $(VENV)
	$(VENV)/bin/pytest -v

clean:
	$(RM) -r build
	$(RM) -r dist
	$(RM) -r $(LADDER_MAP_PACK) $(RAGL_MAP_PACK)
	$(RM) -r oraladder.egg-info
	$(RM) -r venv

$(VENV):
	$(PYTHON) -m venv $@
	$(VENV)/bin/python -m pip install -e .

.PHONY: ladderdev initladderdev wheel clean mappacks ragldev initragldev test
