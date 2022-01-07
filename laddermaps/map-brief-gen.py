import sys
prefix = 'World:\n\tMissionData:\n\t\tBriefing: '
with open(sys.argv[1]) as f:
    brief = f.read()
print(prefix + ' \\n'.join(brief.splitlines()))
