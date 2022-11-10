#%%
start_time_min = 4.0+5/60
# start_time_min = 0.0
mode = 'vis'
# mode = 'dry_run'
# mode = 'save'
input_video_filename = "../piece1/piece1-raw.mp4"
output_video_filename = r'C:\Users\remus\Desktop\piece_1_with_Danmaku-debug.mp4'
comment_filename = '../code_add_comments/chat_01_combined_with_BD_corr.json'
comment_start_time = 00.0 * 60 + 3# + start_time_min*60
# comment_start_time = start_time_min*60 + 3# + start_time_min*60
n_comments_before_zero_time = 10

# input_video_filename = "../piece2/piece2-raw.mp4"
# output_video_filename = r'C:\Users\remus\Desktop\piece_2_no_caption_with_Danmaku_est.mp4'
# comment_filename = '../code_add_comments/chat_01_combined_with_BD_corr.json'
# comment_start_time = 30.0 * 60 + 3# + start_time_min*60
# n_comments_before_zero_time = 10


#%%
from utils import CommentPool
comment_pool_config = {'discard_early_comments': True, 'time_offset': comment_start_time}
# comment_pool_config = {'discard_early_comments': False, 'time_offset': -48}
comment_pool = CommentPool(comment_pool_config)
comment_pool.load_comments_from_json(comment_filename, ['x', '+', '++', '?'], zero_pointer_shift=-n_comments_before_zero_time)
# print('first_comment: ', comment_pool.comments[comment_pool.pointer])


#%% 
from utils import SegmentDanmakuCommentManager
segment_danmaku_comment_manager_config = {
                'layout': 'danmaku',
                'n_tracks': 12,
                'start_time': 0,
                'end_time': -1,
                'font_name': './PingFang SC Bold.ttf',
                'font_size': 40,
                'speed_y': 0,
                'speed_x': '-1.5x',
                # 'speed_x': -10,

                'stroke_width': 3,
                'stroke_fill': (0,0,0,1),
                'track_y_start': 90,
                'track_y_margin': 10,
                'video_H': 1080,
                'video_W': 1920,
                'time_offset': comment_start_time
            }
segment_danmaku_comment_manager = SegmentDanmakuCommentManager(segment_danmaku_comment_manager_config)

#%%
# [python - Getting timestamp of each frame in a video - Stack Overflow](https://stackoverflow.com/questions/47743246/getting-timestamp-of-each-frame-in-a-video)
# [opencv - how to get frames with timestamp where frames are converted from video in python - Stack Overflow](https://stackoverflow.com/questions/51129425/how-to-get-frames-with-timestamp-where-frames-are-converted-from-video-in-python)
# [python opencv get camera frame timestamp in system time accurately - Stack Overflow](https://stackoverflow.com/questions/55069809/python-opencv-get-camera-frame-timestamp-in-system-time-accurately)
# [OpenCV: Getting Started with Videos](https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html)
# [python opencv videocapture get time of frame - Google Search](https://www.google.com/search?q=python+opencv+videocapture+get+time+of+frame&sxsrf=ALiCzsbFdt2ou5k1JDCRk3kwG7mDtqrdXg%3A1665100064912&ei=IGk_Y_GIN93R5NoPuY6D6Ac&ved=0ahUKEwjxmImP5cz6AhXdKFkFHTnHAH0Q4dUDCA4&uact=5&oq=python+opencv+videocapture+get+time+of+frame&gs_lcp=Cgdnd3Mtd2l6EAMyCAghEB4QFhAdOgoIABBHENYEELADOgQIABBDOgUIABCABDoICAAQgAQQywE6BggAEB4QFjoFCAAQhgM6BQghEKABOgUIIRCrAjoHCCEQoAEQCkoFCDwSATFKBAhNGAFKBAhBGABKBAhGGABQrwhYuCBgxCFoAXABeACAAXiIAb8MkgEEMTcuMZgBAKABAcgBCMABAQ&sclient=gws-wiz)
# [Getting specific frames from VideoCapture opencv in python - Stack Overflow](https://stackoverflow.com/questions/33523751/getting-specific-frames-from-videocapture-opencv-in-python)


from utils import CommentDrawer
import numpy as np
from pathlib import Path
import cv2 as cv
# cap = cv.VideoCapture("../code_add_comments/piece_1_no_comment.mp4")
cap = cv.VideoCapture(input_video_filename)
fps = cap.get(cv.CAP_PROP_FPS)
n_total_frames = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
# timestamps = [cap.get(cv.CAP_PROP_POS_MSEC)]
calc_timestamps = [0.0]

# https://stackoverflow.com/questions/33523751/getting-specific-frames-from-videocapture-opencv-in-python

start_frame = start_time_min * 60 *fps
cap.set(cv.CAP_PROP_POS_FRAMES, start_frame)
# comment_pool.set_point_to_time(start_time_min*60, 0)

# Define the codec and create VideoWriter object
if mode == 'save':
    # fourcc = cv.VideoWriter_fourcc(*'XVID')
    # out = cv.VideoWriter('./test_piece_flip.avi', fourcc, 20.0, (640,  480))
    # https://stackoverflow.com/questions/28163201/writing-a-video-file-using-h-264-compression-in-opencv
    # https://stackoverflow.com/questions/61260182/how-to-output-x265-compressed-video-with-cv2-videowriter
    fourcc = cv.VideoWriter_fourcc(*'MP4V')
    # fourcc = cv.VideoWriter_fourcc('a','v','c','1')
    # fourcc = cv.VideoWriter_fourcc(*'H265')
    out = cv.VideoWriter(output_video_filename, fourcc, fps, (1920,1080))
n_minutes = 60/60
# n_minutes = -1
n_frame = int(n_minutes*60*fps) if n_minutes != -1 else n_total_frames
frame_idx = 0 
curr_frame_time = start_time_min*60 + 0.0


comment_drawer_config = {
    # 'text_key': 'content',    
    'font_name': './PingFang SC Bold.ttf',    
    'use_text_mask': False,
    'font_size': segment_danmaku_comment_manager_config['font_size']
}

comment_drawer = CommentDrawer(comment_drawer_config)

text_mask = cv.imread(str('./test_text_mask-6.png'))
text_mask = text_mask.astype(float)/255
# comment_drawer.text_mask = np.ones_like(text_mask)
comment_drawer.text_mask = text_mask
# comment_drawer.text_mask = np.zeros_like(text_mask)


import sys
from time import sleep
from tqdm import tqdm

# while cap.isOpened():
# values = range(3)
all_comment_speeds = []
try:
    with tqdm(total=min(n_total_frames, n_frame), file=sys.stdout) as pbar:
        for frame_idx in range(min(n_total_frames, n_frame)):
            pbar.set_description('frame: %d' % (1 + frame_idx))
            pbar.update(1)
            # sleep(1)

            if n_frame > 0 and frame_idx > n_frame and not cap.isOpened():
                break

            ret, frame = cap.read()
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break
            else:
                # timestamps.append(cap.get(cv.CAP_PROP_POS_MSEC))
                # calc_timestamps.append(calc_timestamps[-1] + 1/fps)
                curr_frame_time += 1/fps
            
            curr_frame_new_comments = comment_pool.get_new_comments_before_time(curr_frame_time)
            # if frame_idx == 0:
                # print('current_time', curr_frame_time)
                # print(len(curr_frame_new_comments))
                # for comment in curr_frame_new_comments:
                #     print(comment)
            segment_danmaku_comment_manager.update_loaded_comments(curr_frame_new_comments, n_comment_limit=10)
            curr_frame_comments = segment_danmaku_comment_manager.get_loaded_comments()

            for track in segment_danmaku_comment_manager.tracks:
                all_comment_speeds += [c.speed_x for c in track.comments]

            if mode != 'dry_run':
                img_with_text = comment_drawer.draw_on_frame(frame, curr_frame_comments)
            else:
                img_with_text = frame
            
            if mode == 'save':
                out.write(img_with_text)
            elif mode == 'vis':
                cv.imshow('frame', img_with_text)
            elif mode == 'dry_run':
                pass
            if cv.waitKey(1) == ord('q'):
                break
    cv.destroyAllWindows()
    cap.release()
    if mode == 'save':
        out.release()
except KeyboardInterrupt:
    cv.destroyAllWindows()
    cap.release()
    if mode == 'save':
        out.release()
        # frame_idx += 1
# Release everything if job is finished

# cv.destroyAllWindows()