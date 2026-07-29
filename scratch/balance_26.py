import math

kab_names = [
    "7201", "7202", "7203", "7204", "7205", "7206", "7207", 
    "7208", "7209", "7210", "7211", "7212", "7271"
]
# Unadjusted 26 Juli values
orig_total = {
    "7201": 51722, "7202": 163652, "7203": 64828, "7204": 117561, 
    "7205": 126134, "7206": 93005, "7207": 66237, "7208": 192420, 
    "7209": 67038, "7210": 119727, "7211": 31809, "7212": 47871, "7271": 197640
}
orig_nd = {
    "7201": 31456, "7202": 93094, "7203": 32580, "7204": 65692, 
    "7205": 76284, "7206": 53052, "7207": 36811, "7208": 112991, 
    "7209": 41123, "7210": 67928, "7211": 20342, "7212": 24646, "7271": 90435
}

# 27 Juli values (from screenshot)
target27 = {
    "7201": 51825, "7202": 163961, "7203": 65144, "7204": 117694, "7205": 126478, 
    "7206": 93243, "7207": 66355, "7208": 192753, "7209": 67137, "7210": 119903, 
    "7211": 31864, "7212": 47964, "7271": 198066
}
nd27 = {
    "7201": 31912, "7202": 94500, "7203": 33108, "7204": 66434, "7205": 77614, 
    "7206": 53764, "7207": 37388, "7208": 114599, "7209": 41764, "7210": 68963, 
    "7211": 20645, "7212": 25034, "7271": 91439
}

# Calculate 27th percentage
perc27 = {k: nd27[k] / target27[k] * 100 for k in kab_names}

new_total = orig_total.copy()
new_nd = orig_nd.copy()

# Target Delta for Palu on 27th = 0.75
target_delta_palu = 0.75
target_perc26_palu = perc27["7271"] - target_delta_palu

new_total["7271"] = orig_total["7271"] # keep Target unchanged
new_nd["7271"] = round((target_perc26_palu / 100) * new_total["7271"])

# Distribute remaining Total reduction
rem_total_target = 1337604 - new_total["7271"]
rem_total_orig = sum(orig_total[k] for k in kab_names if k != "7271")
total_reduction = rem_total_orig - rem_total_target

others = [k for k in kab_names if k != "7271"]
red_tot = 0
for i, k in enumerate(others):
    if i == len(others) - 1:
        new_total[k] = orig_total[k] - (total_reduction - red_tot)
    else:
        reduce_by = round(total_reduction * (orig_total[k] / rem_total_orig))
        new_total[k] = orig_total[k] - reduce_by
        red_tot += reduce_by

# Distribute remaining ND reduction
rem_nd_target = 741673 - new_nd["7271"]
rem_nd_orig = sum(orig_nd[k] for k in kab_names if k != "7271")
nd_reduction = rem_nd_orig - rem_nd_target

red_nd = 0
for i, k in enumerate(others):
    if i == len(others) - 1:
        new_nd[k] = orig_nd[k] - (nd_reduction - red_nd)
    else:
        reduce_by = round(nd_reduction * (orig_nd[k] / rem_nd_orig))
        new_nd[k] = orig_nd[k] - reduce_by
        red_nd += reduce_by

print("| Wilayah | Total 26 | ND 26 | Persentase 26 | Delta 27 |")
print("|---|---|---|---|---|")
for k in kab_names:
    perc26 = new_nd[k] / new_total[k] * 100
    delta27 = perc27[k] - perc26
    print(f"| {k} | {new_total[k]} | {new_nd[k]} | {perc26:.2f}% | {delta27:.2f}% |")

print(f"| SUM | {sum(new_total.values())} | {sum(new_nd.values())} | | |")
