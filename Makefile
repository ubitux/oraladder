PYTHON ?= python
VENV   ?= venv
WGET   ?= wget --no-check-certificate

LADDER_MAP_PACK_VERSION = 2020-12-28
LADDER_MAP_PACK = ladderweb/static/ladder-map-pack-$(LADDER_MAP_PACK_VERSION).zip

RAGL_MAP_PACK_VERSION = 2020-12-28
RAGL_MAP_PACK = raglweb/static/ragl-map-pack-$(RAGL_MAP_PACK_VERSION).zip

ACTIVATE = $(VENV)/bin/activate

ladderdev: initladderdev
	(. $(ACTIVATE) && FLASK_APP=ladderweb FLASK_ENV=development flask run)

initladderdev: $(VENV) $(LADDER_MAP_PACK)
	mkdir -p instance
	$(RM) instance/db.sqlite3
	(. $(ACTIVATE) && ora-ladder -d instance/db.sqlite3)

ragldev: initragldev
	(. $(ACTIVATE) && FLASK_APP=raglweb FLASK_ENV=development flask run)

initragldev: $(VENV) $(RAGL_MAP_PACK)
	mkdir -p instance
	$(RM) instance/db.sqlite3
	(. $(ACTIVATE) && ora-ragl -d instance/db.sqlite3)

wheel: $(VENV)
	(. $(ACTIVATE) && pip install wheel && python setup.py bdist_wheel)

mappacks: $(LADDER_MAP_PACK) $(RAGL_MAP_PACK)

$(LADDER_MAP_PACK): $(VENV)
	(. $(ACTIVATE) && ora-mapstool misc/map-pools/ladder.maps --pack $(LADDER_MAP_PACK))

$(RAGL_MAP_PACK): $(VENV)
	(. $(ACTIVATE) && ora-mapstool misc/map-pools/ragl-s10.maps --pack $(RAGL_MAP_PACK))

clean:
	$(RM) -r build
	$(RM) -r dist
	$(RM) -r $(LADDER_MAP_PACK) $(RAGL_MAP_PACK)
	$(RM) -r oraladder.egg-info
	$(RM) -r venv

$(VENV):
	$(PYTHON) -m venv $@
	( . $(ACTIVATE) && pip install -e .)

.PHONY: ladderdev initladderdev wheel clean mappacks ragldev initragldev
