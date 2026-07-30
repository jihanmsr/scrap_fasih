def calculate_delta_counters(curr_obj, prev_obj, delta_days):
    if not prev_obj:
        prev_obj = {}
        
    def get_bd_val(breakdown, key):
        if not breakdown: return 0
        key_upper = key.upper()
        for k, v in breakdown.items():
            if k.upper() == key_upper: return v
        return 0

    if delta_days == 0:
        curr_obj["yesterday_completed"] = prev_obj.get("yesterday_completed", 0)
        curr_obj["yesterday_completed_breakdown"] = prev_obj.get("yesterday_completed_breakdown", {})
        curr_obj["two_days_ago_completed"] = prev_obj.get("two_days_ago_completed", 0)
        curr_obj["two_days_ago_completed_breakdown"] = prev_obj.get("two_days_ago_completed_breakdown", {})
        curr_obj["two_days_ago_is_estimate"] = prev_obj.get("two_days_ago_is_estimate", False)
        
        b_submitted = prev_obj.get("total_submitted", 0) - prev_obj.get("today_completed", 0)
        b_approved = prev_obj.get("total_approved", 0) - get_bd_val(prev_obj.get("today_completed_breakdown"), "APPROVED BY PENGAWAS")
        b_rejected = prev_obj.get("total_rejected", 0) - get_bd_val(prev_obj.get("today_completed_breakdown"), "REJECTED BY PENGAWAS")
        b_pencacah = prev_obj.get("total_submitted_pencacah", 0) - get_bd_val(prev_obj.get("today_completed_breakdown"), "SUBMITTED BY PENCACAH")
        b_respondent = prev_obj.get("total_submitted_respondent", 0) - get_bd_val(prev_obj.get("today_completed_breakdown"), "SUBMITTED RESPONDENT")
    else:
        if delta_days == 1:
            curr_obj["two_days_ago_completed"] = prev_obj.get("yesterday_completed", 0)
            curr_obj["two_days_ago_completed_breakdown"] = prev_obj.get("yesterday_completed_breakdown", {})
            curr_obj["yesterday_completed"] = prev_obj.get("today_completed", 0)
            curr_obj["yesterday_completed_breakdown"] = prev_obj.get("today_completed_breakdown", {})
        elif delta_days == 2:
            curr_obj["two_days_ago_completed"] = prev_obj.get("today_completed", 0)
            curr_obj["two_days_ago_completed_breakdown"] = prev_obj.get("today_completed_breakdown", {})
            curr_obj["yesterday_completed"] = 0
            curr_obj["yesterday_completed_breakdown"] = {}
        else:
            curr_obj["two_days_ago_completed"] = 0
            curr_obj["two_days_ago_completed_breakdown"] = {}
            curr_obj["yesterday_completed"] = 0
            curr_obj["yesterday_completed_breakdown"] = {}
            
        curr_obj["two_days_ago_is_estimate"] = False
        
        b_submitted = prev_obj.get("total_submitted", 0)
        b_approved = prev_obj.get("total_approved", 0)
        b_rejected = prev_obj.get("total_rejected", 0)
        b_pencacah = prev_obj.get("total_submitted_pencacah", 0)
        b_respondent = prev_obj.get("total_submitted_respondent", 0)

    today_comp = max(0, curr_obj.get("total_submitted", 0) - b_submitted)
    today_bd = {}
    
    inc_approved = max(0, curr_obj.get("total_approved", 0) - b_approved)
    if inc_approved > 0: today_bd["APPROVED BY PENGAWAS"] = inc_approved
        
    inc_rejected = max(0, curr_obj.get("total_rejected", 0) - b_rejected)
    if inc_rejected > 0: today_bd["REJECTED BY PENGAWAS"] = inc_rejected
        
    inc_pencacah = max(0, curr_obj.get("total_submitted_pencacah", 0) - b_pencacah)
    if inc_pencacah > 0: today_bd["SUBMITTED BY PENCACAH"] = inc_pencacah
        
    inc_respondent = max(0, curr_obj.get("total_submitted_respondent", 0) - b_respondent)
    if inc_respondent > 0: today_bd["SUBMITTED RESPONDENT"] = inc_respondent
        
    curr_obj["today_completed"] = today_comp
    curr_obj["today_completed_breakdown"] = today_bd

prev_kab = {
    "total_submitted": 100,
    "today_completed": 10,
    "total_approved": 50,
    "today_completed_breakdown": {"APPROVED BY PENGAWAS": 5}
}
curr_kab = {
    "total_submitted": 120,
    "total_approved": 60,
}

calculate_delta_counters(curr_kab, prev_kab, 1)
print(curr_kab)

