mods = dict(
    ra=dict(
        label='Red Alert',
        icon='icon-ra.png',
        url='https://github.com/OpenRA/OpenRA/releases/tag/release-20210321',
        release='release-20210321',
        supports_analysis=True,
        mappacks=(
            dict(
                label='2021.1 (2021-04-26)',
                filename='ladder-map-pack-2021.1.zip',
                changelog='''
                    Same map pack as 2021.0 with the following changes:
                    <ul>
                        <li>Overlay adjusted to make the minimap more visible</li>
                        <li>Blitz bumped from 1.3 to 1.4 (rev4 to rev5)</li>
                        <li>Kosovo updated to address symmetry issues notably</li>
                        <li>Fix shadowlands extra buildable sandbags (thanks Goremented)</li>
                    </ul>
                ''',
                maps=(),
            ),
            dict(
                label='2021.0 (2021-04-06)',
                filename='ladder-map-pack-2021.0.zip',
                changelog='''
                    This pack is a selection of 15 maps curated by the RA
                    Competitive Maps Committee to celebrate the end of RAGL. It
                    includes a few popular old maps and some brand new. The
                    balance is the same as previously (affecting Ranger, Dome
                    and LongBow) with an additional fix for the missing phase
                    transport sound notification. ERCC 2.1/BCC 1.0 modding is
                    also still present.
                ''',
                maps=(
                    ('Blitz', 'kazu'),
                    ('Breaking Bad', 'Goremented'),
                    ('Clover', 'Lad'),
                    ('Crownsbury', 'Pinkthoth'),
                    ('Eden Lake', 'kazu'),
                    ('Eternal Warriors', 'J MegaTank'),
                    ('Forgotten Plains', 'eskimo'),
                    ('Kosovo', 'poop'),
                    ('Marigold Town', 'Super Newbie'),
                    ('Mountain Range Redux', 'Blackend'),
                    ('Offensive Operation', 'Lad'),
                    ('Onyx', 'eskimo'),
                    ('Shadowlands', 'Lad'),
                    ('Styx', 'Pinkthoth'),
                    ('Treasure Hunt', 'Lad'),
                ),
            ),
            dict(
                label='2021-03-29',
                filename='ladder-map-pack-2021-03-29.zip',
                changelog='''
                    Temporarily removed the S9 maps as they are causing too much
                    crashes. Only RAGL X maps remain.
                ''',
                maps=(
                    ('Amsterdamned[RAGL-X]', 'wippie'),
                    ('Annihilate[RAGL-X]', 'poop'),
                    ('Behind The Curtain[RAGL-X]', 'WhoCares & Kyrylo Silin'),
                    ('Darkside Aftermath[RAGL-X]', 'J MegaTank'),
                    ('Devils Marsh[RAGL-X]', 'N/a'),
                    ('Mounds[RAGL-X]', 'Pinkthoth'),
                    ('Nomad[RAGL-X]', 'Upps'),
                    ('Off My Lawn, Punks ![RAGL-X]', 'WhoCares & Hamb'),
                    ('Pitfight[RAGL-X]', 'kazu.'),
                    ('Polemos[RAGL-X]', 'KOYK'),
                    ('Timian[RAGL-X]', 'Widow'),
                    ('Winding Woods[RAGL-X]', 'Pinkthoth'),
                ),
            ),
            dict(
                label='2020-12-28',
                filename='ladder-map-pack-2020-12-28.zip',
                changelog='''
                    <strong>Warning</strong>: this map pack contains broken S9
                    maps: the light tank husks will cause crashes.
                ''',
                maps=(
                    ('Agita RAGL S9', 'kazu.'),
                    ('Amsterdamned[RAGL-X]', 'wippie'),
                    ('Annihilate[RAGL-X]', 'poop'),
                    ('Behind The Curtain[RAGL-X]', 'WhoCares & Kyrylo Silin'),
                    ('Darkside Aftermath[RAGL-X]', 'J MegaTank'),
                    ('Devils Marsh[RAGL-X]', 'N/a'),
                    ('Discovery RAGL S9', 'Lad'),
                    ('Dual Cold Front RAGL S9', 'PizzaAtomica'),
                    ('Mounds[RAGL-X]', 'Pinkthoth'),
                    ('Mountain Ridge Redux RAGL S9', 'Blackened'),
                    ('Nomad[RAGL-X]', 'Upps'),
                    ('Off My Lawn, Punks ![RAGL-X]', 'WhoCares & Hamb'),
                    ('Ore Egano RAGL S9', 'kazu.'),
                    ('Pitfight[RAGL-X]', 'kazu.'),
                    ('Polemos[RAGL-X]', 'KOYK'),
                    ('Shadowfiend II RAGL S9', 'kazu.'),
                    ('Sonora RAGL S9', 'wippie'),
                    ('Teared Strait RAGL S9', 'mo'),
                    ('The Swamp RAGL S9', 'kazu.'),
                    ('Three and a half woods RAGL S9', "WhoCares (based on SN's Seventh woods)"),
                    ('Timian[RAGL-X]', 'Widow'),
                    ('Trail of Thought RAGL S9', 'netnazgul'),
                    ('Wetlands RAGL S9', 'i like men'),
                    ('Winding Woods[RAGL-X]', 'Pinkthoth'),
                ),
            ),
        ),
    ),
    td=dict(
        label='Tiberian Dawn',
        icon='icon-td.png',
        url='https://github.com/OpenRA/OpenRA/releases/tag/release-20210321',
        release='release-20210321',
        mappacks=(
            dict(
                label='2021-04-05',
                filename='ladder-map-pack-td-2021-04-05.zip',
                changelog='''
                    First map pack with TDGL2+ maps (minus the disliked
                    <strong>Masters Frontline</strong>) and custom balance
                    removed.
                ''',
                maps=(
                    ('16:9[Ladder]', 'norman'),
                    ('African Gambit[Ladder]', 'MASTER, Jay'),
                    ('Badland Ridges[Ladder]', 'The Echo of Damnation'),
                    ('CrackPoint[Ladder]', 'MASTER'),
                    ('Desert Mandarins[Ladder]', 'MASTER'),
                    ('Tiberium Rift[Ladder]', 'ZxGanon'),
                ),
            ),
        ),
    ),
)
