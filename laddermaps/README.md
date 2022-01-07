# Ladder map pack

This document describes the procedure to build and deploy a new map pack on the
ladder.


## Step 1: preparing the maps, overlay and briefing

### Short version

1. update `maps.list`
2. update version in `Makefile`
3. update `ladder-briefing.txt`
4. run `make clean && make`

### Long version

1. Adjust the `maps.list` file in this directory to contain the list of map
   URLs to download as source: these maps are the "vanilla" source maps.
2. Edit the `Makefile` in this directory to adjust the `OVERLAY_VERSION`. The
   versioning scheme currently used is `<YEAR>.<REVISION>`. For example,
   `2021.3` would be the 3rd iteration of the map pack for the year 2021. Every
   time a map has to be added, removed or simply patched, the `<REVISION>`
   *MUST* be incremented. When we reach a new year, the `<REVISION>` *MUST* be
   reset to `0`.
3. Adjust the `ladder-briefing.txt` file to summarize what will differ from
   vanilla OpenRA in the maps (every balance modding basically)
4. Make sure the following dependencies are available on your system:
    - ImageMagick (you should have a `magick` program): it is used to generate
      the overlay image
    - wget (it is used to download all the maps)
    - Python3 (it is used for various utils)
5. Run `make clean` if it's not your first run, then `make`

If everything went right, you should now have the following available:
- all the source maps in the `source-maps` directory
- an `overlay.png` picture that is meant to be overlayed on every map preview
- a `extensions/ladder-brief/ladder-briefing.yaml` file to be used for modding
  every map


## Step 2: updating the extensions

The `extensions` directory must be updated with all the balance mods. The
unused extensions *MUST* be removed. Beware not to remove `ladder-brief`.

Each extension is in a directory `extensions/<NAME>` where `<NAME>` is an
arbitrary name of your choice. In this directory, all the yaml files are
dumped. In that same directory, an `_extension.yaml` file must be created to
contain `Rules:`, `Sequences:`, etc references.

Two things to be aware of:

1. do not delete the `ladder-brief` extension
2. make sure the extensions do not contain briefing rules
3. lobby rules extensions are not needed on the ladder, they are configured on
   the server, so you must remove them to prevent any conflict


## Step 3: packaging the maps

For this step you will need the [ora-tools](https://github.com/ubitux/oratools).

Assuming you entered the `ora-tools` Python virtualenv, adjust and run the
following commands:

```sh
export LADDERMAPS_DIR=/path/to/oraladder/laddermaps  # Adjust this!
export LADDERMAPS_VERSION=YYYY.RR # Adjust this!
ora-tool mappack \
    --overlay $LADDERMAPS_DIR/overlay.png \
    --strip-tags \
    --ext $LADDERMAPS_DIR/extensions/* \
    --rm ragl-briefing-rules.yaml lobby-rules.yaml ERCC2-rules.yaml ercc2-rules.yaml ERCC2-sequences.yaml ercc2-sequences.yaml ragl-balance.yaml ragl-briefing.yaml ragl-weapons.yaml ERCC21andBCC-rules.yaml briefing.yaml briefing-rules.yaml bain2-rules.yaml bain2-weapons.yaml ragl-actor-rules.yaml ragl-actor-sequences.yaml ragl-balance-rules.yaml tox_sign.shp .DS_Store harv-flipped_top.shp ref-anim.shp ref-bot.shp ref-top.shp \
    --title '{title} [ladder]' \
    --category Ladder-$LADDERMAPS_VERSION \
    --out-dir /tmp/ladder-maps \
    $LADDERMAPS_DIR/source-maps
```

Explanations:

- `--overlay`: path to the `overlay.png` image previously created
- `--strip-tags`: clean existing tags in source maps
- `--ext`: select all the extensions we want to add to all maps
- `--rm`: will try to remove to all these files (and their references) from
  each of the source maps: this one is important, you must inspect each run of
  the command and make sure you removed existing modding that may conflict with
  your extensions (look in particular at the `Copy` entries when running the
  command)
- `--title`: currently adds a `[ladder]` tag to the maps to differentiate them
  from the vanilla ones
- `--category`: useful for players to be able to filter the proper map pack
  from the `Category` drop-down menu in OpenRA
- `--out-dir`: this is the destination directory of the patched maps, you can
  specify whatever you want


## Step 4: finalization

- make sure all the patched maps are working as expected
- upload them on https://resource.openra.net/
- commit all the changes in a dedicated commit
- update `misc/map-pools/ladder.maps` with the IDs of the newly uploaded maps
- run `ora-mapstool misc/map-pools/ladder.maps --pack
  ladderweb/static/ladder-map-pack-XXX.zip` (adjust `XXX`) to make a new pack
- update `ladderweb/mods.py` so that it's available on the website
- make a second commit with these changes

The repository is now ready to be synchronized with production.
