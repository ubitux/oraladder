OVERLAY_VERSION = 2022.0

PYTHON = python3
MAGICK = magick
WGET = wget

OVERLAY_FILE = overlay.png
BRIEF_EXT_YAML = extensions/ladder-brief/ladder-briefing.yaml

ALL = $(OVERLAY_FILE) $(BRIEF_EXT_YAML) source-maps

all: $(ALL)

source-maps: maps.list
	$(WGET) -i maps.list --continue --content-disposition --directory-prefix $@

$(OVERLAY_FILE):
	$(MAGICK) -size 200x200 xc:none -font 'Noto-Sans-Mono-Condensed-Black' \
		-pointsize 38 -fill '#D93D29' -stroke white \
		-gravity north-west -annotate 0x0 "Ladder" \
		-gravity south-east -annotate 0x0 "$(OVERLAY_VERSION)" \
		$@

$(BRIEF_EXT_YAML): ladder-briefing.txt
	$(PYTHON) map-brief-gen.py $^ > $@

clean:
	$(RM) $(OVERLAY_FILE)
	$(RM) $(BRIEF_EXT_YAML)
	$(RM) -r source-maps

.PHONY: all clean
