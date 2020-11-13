import scaleapi

'''
Overall architecture

Test filters for:
-Correct flagging on current image
    -have filter return the id of attribute for a picture
-false positive flagging on other images
    -have filter return id of attributes of other pictures

must pass first picture before checking others
if other images present the same flagging, check them for accuracy
    -save the results to check for false positives or positive flags
        -save to another file
    -use results to benchmark accuracy
    -a high count of false positives in other photos suggests using a different approach to filtering
    -accurate = definite error
    -inaccurate = warning

filters go into specific pictures, print out results
    -modify until flagging correctly - user input
    -want high accuracy - not sure if approval here can be programatic
then use filter with other images
    -print results to file with some specifying name
    -add lines to file to flag for accurate or false positive
    -run program to read for false positive and count it -> get accurate vs FP

print result of filter (accuracy/fp in main, accuracy/fp in other pics)


at scale:
-filter checking with other pictures may check subset based on speed of scans



'''

# Gets annotations and puts into map with UUID as key
def get_task_annots(client, task_id):
    task = client.fetch_task(task_id)
    uuid_map = {}
    for annot in task.response['annotations']: #TODO MEM
        uuid_map[annot['uuid'][-4:]] = annot
    return [task_id, uuid_map]


'''
    Creating Filter for 5f127
    want to flag some traffic_control_signs as information_signs
    -could check for square like image(based on tilt)
    -could check for width height ratio being lower than that of a traffic light
        -use traffic light as control
    '''
    
# Get control value for H/W ratio of actual traffic signs to compare to info_signs
def hyp_20ad(annots):
    #Hypothesis: height/width ratio of info signs < h/w of actual traffic signs
    #Calculate the control ratio of all true traffic control signs in pic

    #Traffic sign
    s1 = annots['9b3e']
    hw1 = s1['height']/s1['width']
    #print(hw1)
    
    #Traffic sign
    s2 = annots['cb08']
    hw2 = s2['height']/s2['width']
    #print(hw2)
    
    s3 = annots['7238']
    hw3 = s3['height']/s3['width']

    min_ratio = min(hw1, hw2, hw3)
    print("Control Sample Data")
    print([s1, s2, s3])
    print()
    return min_ratio

# Apply hypothesis control value to all annotations
def hyp_20ad_filter1(annots, filter):
    #Filter is control value of real traffic control signs
    is_fp = {}

    #Check for traffic control sign with a smaller h/w ratio & fag
    for uuid in annots.keys():
        annot = annots[uuid]
       
        if annot['label'] == 'traffic_control_sign' and (annot['attributes']['background_color'] == 'other' or annot['attributes']['background_color'] == 'not_applicable'):
            cur_hw = annot['height']/annot['width']
            is_fp[uuid] = [False, cur_hw]
            if cur_hw < filter and cur_hw >= 0.9655172413793104:
                is_fp[uuid][0] = True

    #These are false positives
    
    
    return is_fp

def count_fp_fn(is_fp, tot_annot, should_be_true_keys):
    fp = 0
    fn = 0
    for key in is_fp.keys():
        if is_fp[key][0] == True:
            if key in should_be_true_keys:
                print("True, "+ key + " " + str(is_fp[key]))
                fp += 1
            else:
                print("False, "+ key + " " + str(is_fp[key]))
                fn += 1
    print(str(fp) + " fps detected out of " + str(len(should_be_true_keys)) + " should be true")
    print("true false positive coverage is :" + str(fp/len(should_be_true_keys)))
    print("improper exclusion is: " + str(fn/(tot_annot - len(should_be_true_keys))))
    print()

def count_true(is_fp, tot_annot):
    true = []
    for key in is_fp.keys():
        if is_fp[key][0] == True:
            true.append([key, is_fp[key][1]])
    return true


'''
Try with other annotations, return true % and check them
'''

def main():
    task_ids = ['5f127f6f26831d0010e985e5', '5f127f6c3a6b1000172320ad', '5f127f699740b80017f9b170', '5f127f671ab28b001762c204', '5f127f643a6b1000172320a5', '5f127f5f3a6b100017232099', '5f127f5ab1cb1300109e4ffc', '5f127f55fdc4150010e37244']
    client = scaleapi.ScaleClient('')
    all_task_annot = [get_task_annots(client, task_annot) for task_annot in task_ids]

    #Test for 20ad
    t1 = all_task_annot[1][1]
    filter = hyp_20ad(t1)
    print("Baseline h/w ratio is: " + str(filter))
    is_fp = hyp_20ad_filter1(t1, filter)
    should_be_true_keys = ['e3ee', 'cad4', '88cd', 'b793']
    count_fp_fn(is_fp, len(t1.keys()), should_be_true_keys) #Returns all correct
    for i in range(len(task_ids)):
        annots = all_task_annot[i][1]
        uuid = all_task_annot[i][0]
        if i != 1:
            true_ids = count_true(hyp_20ad_filter1(annots, filter), len(annots))
            print(uuid + " had " + str(len(true_ids)) + " trues out of " + str(len(annots)) + " total annotations")
            print(true_ids)

    

main()


'''
Notes:

Could not detect undetected signs in 20a5


5f127f643a6b1000172320a5 had 1 trues out of 11 total annotations
[['b08c', 0.35294117647058826]] - very wide


need to check whether they are false positives to be flagged or not, some just wider than is tall
'''