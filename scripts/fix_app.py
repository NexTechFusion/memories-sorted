with open('web/app.html', 'r') as f:
    lines = f.readlines()

# Line numbers are 1-indexed
# Remove duplicate addMoment modal that uses addMoment.show (lines 40-52)
# Remove duplicate momentEdit modal (lines 118-127) 
# Remove first doAddMoment duplicate (lines 555-563)
# The doSaveCaption fix was already applied inline

skip_ranges = [
    (40, 52),   # duplicate addMoment with addMoment.show
    (118, 127), # duplicate momentEdit modal
    (555, 563), # first doAddMoment duplicate
]

new_lines = []
for i, line in enumerate(lines):
    ln = i + 1
    if any(start <= ln <= end for start, end in skip_ranges):
        continue
    new_lines.append(line)

with open('web/app.html', 'w') as f:
    f.writelines(new_lines)

content = ''.join(new_lines)
print(f"Fixed! Lines: {len(new_lines)} (was {len(lines)})")
# Check key markers
for m in ['app(){return{', 'doSaveCaption', 'init()', 'lbZoomStart', 'doAddMoment', '</script>']:
    print(f"  {m}: {content.count(m)}")
