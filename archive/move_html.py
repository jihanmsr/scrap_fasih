import sys

def move_granular_section(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_idx = -1
    end_idx = -1

    # find <div ... id="granular-assignment-section-wrapper">
    for i, line in enumerate(lines):
        if 'id="granular-assignment-section-wrapper"' in line:
            start_idx = i
            # search backwards for the previous comment to include it
            if "<!-- Granular Target / Assignment Section -->" in lines[i-1]:
                start_idx = i - 1
            break
            
    if start_idx == -1:
        print("Could not find start")
        return

    # find the end of this div. It ends right before "<!-- Petugas Section -->" or a similar marker.
    for i in range(start_idx, len(lines)):
        if "<!-- Petugas Section -->" in lines[i]:
            end_idx = i - 1  # excluding the closing div of tab-content-assign or whatever is there
            # actually, granular-assignment-section-wrapper is just a div.
            # let's just find the closing </div> for it.
            # We can count divs.
            break

    if end_idx == -1:
        print("Could not find end")
        return
        
    # We found the block! Let's be precise.
    # The block ends around line 1005 (where <!-- Petugas Section --> is at 1007)
    # Let's count open/close divs to find the exact end of granular-assignment-section-wrapper
    open_divs = 0
    found_start = False
    real_end_idx = -1
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if 'id="granular-assignment-section-wrapper"' in line:
            found_start = True
        
        if found_start:
            open_divs += line.count('<div')
            open_divs -= line.count('</div')
            
            if open_divs == 0:
                real_end_idx = i
                break
                
    if real_end_idx == -1:
        print("Could not balance divs")
        return

    extracted = lines[start_idx:real_end_idx+1]
    
    # Remove it from original
    new_lines = lines[:start_idx] + lines[real_end_idx+1:]
    
    # Now insert it at the end, right before <div class="tab-content" id="tab-content-email" or similar, 
    # or just right before the closing </main>
    
    # Let's find </main>
    main_end_idx = -1
    for i, line in enumerate(new_lines):
        if '</main>' in line:
            main_end_idx = i
            break
            
    if main_end_idx == -1:
        print("Could not find </main>")
        return
        
    tab_content = [
        '            <div class="tab-content" id="tab-content-target" style="display: none; padding: 1.5rem;">\n'
    ] + extracted + [
        '            </div>\n'
    ]
    
    new_lines = new_lines[:main_end_idx] + tab_content + new_lines[main_end_idx:]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("Successfully moved granular section!")

move_granular_section('index.html')
