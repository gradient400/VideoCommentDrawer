import json
class Comment:
    def __init__(self, content, upper_left_y=0, upper_left_x=0, height=-1, width=-1, speed_y=0, speed_x=-1, font_size=40):
        self.content = content
        self.upper_left_y = upper_left_y
        self.upper_left_x = upper_left_x
        self.font_size = font_size
        self.height = height
        self.width = width
        self.speed_y = speed_y # Distence between two frames
        self.speed_x = speed_x
        self.time = 0.0

    def move(self, steps = 1):
        self.upper_left_y += self.speed_y * steps
        self.upper_left_x += self.speed_x * steps

    def __str__(self):
        return str(self.content)

    # def to_dict(self):
    #     return {
    #         'content': self.content,
    #         'upper_left_'
    #     }
    
    # def _repr_html_(self):
    #     return vars(self)


class CommentPool:
    def __init__(self, config):
        self.config = config
        self.time_offset = config.get('time_offset', 0)
        self.pointer = 0
        self.comments = []
        # self.on_screen_comments = []

    def load_comments_from_json(self, json_filename, filter_keywords=None, zero_pointer_shift=0):
        raw_comments = json.load(open(json_filename, encoding="utf-8"))
        # if filter_keywords is None:
        #     self.comments = raw_comments
        # else:
        self.comments = []
        for raw_comment in raw_comments:
            try:
                if len(raw_comment['Man']) < 0:
                    continue
                elif raw_comment['Man'] == '0':
                    raw_comment['Man'] = raw_comment['content']
                elif raw_comment['Man'] == '1':
                    raw_comment['Man'] = raw_comment['tG']
                elif raw_comment['Man'] == '2':
                    raw_comment['Man'] = raw_comment['tD']
                elif raw_comment['Man'] == '3':
                    raw_comment['Man'] = raw_comment['tBD']
                elif raw_comment['Man'] == '?':
                    continue
                elif raw_comment['Man'] in filter_keywords:
                    continue
            except:
                print(raw_comment)
                break
            self.comments.append(raw_comment)
        
        self.zero_time_pointer = self.get_zero_time_pointer(zero_pointer_shift)
        self.reset_pointer()
    
    def get_comments_at_time(self, time):
        pass

    def set_point_to_time(self, time, n_pre_load):
        pointer = 0
        for pointer in range(len(self.comments)):
            if self.comments[pointer]['time_raw'] <= time + self.time_offset:
                pointer += 1
            else:
                break
        self.pointer = max(0, pointer - n_pre_load)
        

    def get_new_comments_before_time(self, time, from_head=False, n_pre_load=0):
        """Get new comments before given time

        Args:
            time (float or int): _description_

        Returns:
            new_comments: new comments before give time
        """
        new_comments = []
        if from_head:
            current_pointer = 0
        else:
            current_pointer = self.pointer
        for pointer in range(max(current_pointer-n_pre_load, 0), len(self.comments)):
            if self.comments[pointer]['time_raw'] <= time + self.time_offset:
            # if self.comments[pointer]['time_raw'] <= time:
                new_comments.append(self.comments[pointer])
                self.pointer += 1
            else:
                break
        return new_comments

    def set_pointer_to_time(self, time, start_position=None):
        if start_position is None:
            start_position = self.pointer
        
        for pointer in range(start_position, len(self.comments)):
            if self.comments[pointer]['time'] <= time + self.time_offset:
                self.pointer += 1
            else:
                break

    def get_zero_time_pointer(self, shift=0):
        self.zero_time_pointer = 0
        for pointer in range(0, len(self.comments)):
            if self.comments[pointer]['time_raw'] < self.time_offset:
                self.zero_time_pointer += 1
            else:
                break
        return max(pointer + shift, 0)
    
    def reset_pointer(self):
        if self.config.get('discard_early_comments', False):
            self.pointer = self.zero_time_pointer
        else:
            self.pointer = 0
    
    def clear(self):
        self.reset_pointer()
        self.comments = []
    
    def __len__(self):
        return len(self.comments)

    def __getitem__(self, idx):
        return self.comments[idx]
    

class SegmentListCommentManager:
    def __init__(self, config):
        self.comments = []
        if config is None:
            config = {
                'layout': 'list',
                'queue_length': 10,
                'start_time': 0,
                'end_time': -1,
                'font_name': './PingFang SC Bold.ttf',
                'font_size': 30,
                'y_shift': 15,
                'line_width_pixel': 320,
                'line_width_char': 10,
                'stroke_width': 3,
                'stroke_fill': (0,0,0,1)
            }
        self.config = config
    
    def load_config_from_json(self, json_filename):
        self.config = json.load(open(json_filename, encoding="utf-8"))

    def update_loaded_comments(self, new_comments=None, config=None):
        if new_comments is None:
            new_comments = []
        if config is None:
            config = self.config

        new_comments = [Comment(new_comment) for new_comment in new_comments]
        
        self.comments += new_comments
        self.comments = self.comments[-min(config['queue_length'], len(self.comments)):]

        # Update comment location - skipped here
        for comment in self.comments:
            pass

    def __str__(self):
        return str([str(comment) for comment in self.comments])

EMPTY = 0
OCCUPIED = 1

class DanmakuTrack:
    def __init__(self, upper_y=0, video_W=1920, time_offset = 0):
        self.comments = []
        self.idx = -1
        self.starting_line_occupied = False        
        self.upper_y = upper_y
        self.video_W = video_W
        self.margin = 60
        self.time_offset = time_offset

        self.all_full_triggered = False
    
    def check_starting_line_occupied(self):
        if len(self.comments) == 0:
            return False
        # elif len(self.comments)>0 and self.comments[-1].upper_left_x + self.comments[-1].width + self.margin < self.video_W:
        #     return False
        elif all([comment.upper_left_x + comment.width + self.margin < self.video_W for comment in self.comments]):
            return False
        else:
            return True
    
    def update_starting_line_occupied(self):
        self.starting_line_occupied = self.check_starting_line_occupied()

    def move(self, steps=1):
        # Let the existing comments to move
        for comment in self.comments:
            comment.move(steps)
        
        # pop the our-of-screen ones
        # only need to care about the leftmost comment
        # if len(self.comments)>0 and self.comments[0].upper_left_x + self.comments[0].width < 0:
        #     self.comments.pop(0)
            # print(f'pop, len {len(self.comments)}')
        comment_indices_to_pop = []
        for comment_idx, comment in enumerate(self.comments):
            if comment.upper_left_x + comment.width < 0:
                comment_indices_to_pop.append(comment_idx)
        for comment_to_pop_idx in comment_indices_to_pop[::-1]:
            self.comments.pop(comment_to_pop_idx)

        
        # Check whether the latest comment leaves the starting line
        # if len(self.comments)>0 and self.comments[-1].upper_left_x + self.comments[-1].width + self.margin < self.video_W:
        #     self.starting_line_occupied = False
        self.starting_line_occupied = self.check_starting_line_occupied()
    
    def add_comment(self, new_comment, random_shift_early_comments=True):
        # Should receive only one new comment
        new_comment.upper_left_y = self.upper_y
        new_comment.upper_left_x = self.video_W
        
        if new_comment.time < self.time_offset and random_shift_early_comments:
            new_comment.upper_left_x += np.random.randint(1000) - 500
        # print('new_comment from track', new_comment)
        self.comments.append(new_comment)

        self.starting_line_occupied = True

    def count_out_of_screen(self):
        count = 0
        for comment in self.comments:
            if comment.upper_left_x + comment.width < 0:
                count += 1
        return count

class SegmentDanmakuCommentManager:
    def __init__(self, config):
        # Need drawing info because it's needed to determine which track is empty
        # self.comments = []
        if config is None:
            config = {
                'layout': 'danmaku',
                'n_tracks': 15,
                'start_time': 0,
                'end_time': -1,
                'font_name': './PingFang SC Bold.ttf',
                'font_size': 40,
                'speed_y': 0,
                # 'speed_x': '-2.5x',
                'speed_x': -5,
                'stroke_width': 3,
                'stroke_fill': (0,0,0,1),
                'track_y_start': 40,
                'track_y_margin': 10,
                'video_H': 1080,
                'video_W': 1920
            }
        self.config = config
        self.tracks = []
        self.comment_buffer = []
        self.all_full_triggered = False
        self.font = ImageFont.truetype(self.config['font_name'], self.config['font_size'])
        _, self.track_height = self.font.getsize('测试文字')
        for track_idx in range(self.config['n_tracks']):
            new_track = DanmakuTrack(config['track_y_start'] + track_idx * self.track_height + self.config['track_y_margin'], 1920, time_offset=config.get('time_offset', 0))
            new_track.idx = track_idx
            self.tracks.append(new_track)
    
    def load_config_from_json(self, json_filename):
        self.config = json.load(open(json_filename, encoding="utf-8"))

    def convert_speed(self, raw_speed, text_width:int = 1) -> float:
        if type(raw_speed) is str and raw_speed.endswith('x'):
            speed_times = float(raw_speed[:-1])
            speed = text_width*speed_times
        elif type(raw_speed) in [int, float]:
            speed = raw_speed
        else:
            raise ValueError(f'Unrecognized speed setting: {raw_speed}')
        return speed


    def update_loaded_comments(self, raw_new_comments=None, steps=1, n_comment_limit = -1):
        # print(raw_new_comments)
        # Update the location of all existing comments in each track
        # print('move')
        for track in self.tracks:
            track.move(steps)

        # if self.all_full_triggered:
        #     print([track.starting_line_occupied for track in self.tracks])
        
        # Make new_comments empty list if None
        if raw_new_comments is None:
            raw_new_comments = []
        
        if n_comment_limit > 0:
            raw_new_comments = raw_new_comments[-n_comment_limit:]
        
        # Combine the previous unloaded comments and new comments
        # print('buffer + new')
        new_comments = []
        for raw_new_comment in raw_new_comments:
            # new_comment = Comment(raw_new_comment['content'])
            new_comment = Comment(raw_new_comment['Man'])
            new_comment.time = float(raw_new_comment['time_raw'])
            new_comment.width, new_comment.height = self.font.getsize(new_comment.content)            
            new_comment.font_size = self.config['font_size']
            new_comment.speed_y = self.convert_speed(self.config.get('speed_y', 0))
            new_comment.speed_x = min(-10, self.convert_speed(self.config.get('speed_x', -1), len(new_comment.content)))
            new_comments.append(new_comment)

        comments_to_be_loaded = self.comment_buffer + new_comments
        # print([c.content for c in comments_to_be_loaded])

        # Try load the comments
        # print('loading')
        for new_comment_idx, new_comment in enumerate(comments_to_be_loaded):
            comment_loaded = False
            for track_idx, track in enumerate(self.tracks):
                # if there exists an empty track, load the comment there
                if not track.starting_line_occupied:
                    # print('new_comment from manager', new_comment)
                    track.add_comment(new_comment)
                    comment_loaded = True
                    break
            
            # if there's no empty track for current comment, move this and all later comments to buffer
            if comment_loaded == False:
                # self.comment_buffer = comments_to_be_loaded[new_comment_idx:]
                # self.all_full_triggered = True
                # print('buffer len: ', len(self.comment_buffer))
                break
        # print('current buffer length: ', len(self.comment_buffer))
        
        
    def get_loaded_comments(self):
        loaded_comments = []
        for track in self.tracks:
            loaded_comments += track.comments
        return loaded_comments
        

class SegmentsCommentManager:
    def __init__(self, config):
        self.config = config

    def get_comments_at_time(self, time):
        pass

    def get_current_comments(self):
        pass

import json
import numpy as np
from copy import copy
from PIL import ImageFont, ImageDraw, Image
import textwrap
import colorsys
# textwrap.wrap('123456', 2)
class CommentDrawer:
    def __init__(self, config):
        self.config = config
        self.text_key = config.get('text_key', 'Content')
        self.random_chars = '杩欎釜椤甸潰涓昏鐢ㄦ潵瑙傚療涓�娈垫枃瀛楋紙闈炶嫳鏂囷級鍦ㄧ紪鐮侀敊璇椂鐨勬樉绀烘儏鍐碉紝鍘熺悊鏄互UTF-8缂栫爜璇诲彇杈撳叆鐨勬枃瀛楋紝鐒跺悗浠ラ�夊畾鐨勭紪鐮佹樉绀恒�傚彲閫夌殑閮芥槸鏈湴鍖栫紪鐮侊紝瀹冧滑鍧囦笌UTF-8缂栫爜涓嶅吋瀹癸紙涓嶅寘鍚緭鍏ョ殑瀛楃锛屾垨铏藉寘鍚絾鐮佷綅涓嶄竴鑷达級锛屾墍浠ヤ細閫犳垚涔辩爜銆傝�屽綋杈撳叆绾嫳鏂囨椂锛屾棤璁洪�夋嫨鍝缂栫爜閮借兘姝鏄剧ず涓嶄細涔辩爜銆傝繖鏄洜涓哄畠浠兘鍏煎鑻辨枃鎵�鍦ㄧ殑ASCII鐮佷綅锛堢爜浣嶄竴鑷达級銆�'
    
    def wrap_text(self, text, length):
        wrapped_text_lines = []
        n_splitted_lines = len(text)//length+1 if len(text) % length != 0 else len(text)//length
        for wrapped_text_line_idx in range(n_splitted_lines):
            wrapped_text_lines.append(text[wrapped_text_line_idx*length: min(len(text), (wrapped_text_line_idx+1)*length)])
        return wrapped_text_lines

    def set_text_mask(self, mask):
        if type(mask) is np.ndarray:
            self.text_mask = mask
        elif type(mask) is str:
            pass

    def wrap_comments(self, comments, line_width):
        # Note: text wrapping may not work properly with Chinese sentences. So I implemented my version
        comments_warpped = []
        for comment_idx, comment in enumerate(comments):
            # comment_wrapped_lines = textwrap.wrap(comment[self.text_key], line_width)
            comment_wrapped_lines = self.wrap_text(comment[self.text_key], line_width)
            for comment_wrapped_line_idx, comment_wrapped_line in enumerate(comment_wrapped_lines):
                comment_wrapped_line_dict = copy(comment)
                comment_wrapped_line_dict[self.text_key] = comment_wrapped_line if comment_wrapped_line_idx == 0 else '  ' + comment_wrapped_line
                comments_warpped.append(comment_wrapped_line_dict)
        return comments_warpped

    def sample_average_color_in_range(self, frame, config=None):
        if config is None:
            config = {
                'range':{
                    'upper_left_y': 1*frame.shape[0]//10,
                    'upper_left_x': 3*frame.shape[1]//4,
                    'height': 1*frame.shape[0]//2,
                    'width': 1*frame.shape[1]//4
                }
            }
        frame_height, frame_width, _ = frame.shape
        region_range = config['range']
        region_of_frame = frame[
            region_range['upper_left_y']:min(region_range['upper_left_y'] + region_range['height'], frame_height),
            region_range['upper_left_x']:min(region_range['upper_left_x'] + region_range['width'], frame_width),
            :]
        
        region_average_color_rgb = list(np.mean(region_of_frame, axis=(0,1))/255)

        HUE = 0
        LIGHTNESS = 1
        SATURATION = 2        
        region_average_color_hls = colorsys.rgb_to_hls(*region_average_color_rgb)
        region_average_color_hls_corrected = list(region_average_color_hls)
        if region_average_color_hls[LIGHTNESS] < 0.05:
            # If too dark, Make it gray: SAT > 0.75, SAT=0, HUE = arbitary
            region_average_color_hls_corrected[SATURATION] = 0
            region_average_color_hls_corrected[LIGHTNESS] = 0.95
        else:
            region_average_color_hls_corrected[SATURATION] = max(region_average_color_hls_corrected[SATURATION], 0.7)
            region_average_color_hls_corrected[LIGHTNESS] = max(region_average_color_hls_corrected[LIGHTNESS], 0.8)
        region_average_color_rgb_corrected = [int(ch*255) for ch in colorsys.hls_to_rgb(*region_average_color_hls_corrected)]

        return region_average_color_rgb_corrected

    def random_error_char(self, text):
        # randomly replace character in text with error char
        # https://www.qqxiuzi.cn/zh/luanma/
        # https://lab.sp88.com.tw/genpass/
        pass

    
    def draw_on_frame(self, frame, comments, new_config=None):
        # https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Drawing_text
        # https://stackoverflow.com/questions/47123649/pil-draw-transparent-text-on-top-of-an-image
        if new_config is None:
            config = self.config
        else:
            config = copy(self.config)
            config.update(new_config)

        dynamic_font_color = config.get('dynamic_font_color', True)
        # dynamic_font_color_sample_region = config.get('dynamic_font_color_sample_region', None)
        
        font_name = config.get('font_name', './PingFang SC Bold.ttf')
        font_size = config.get('font_size', 40)
        font = ImageFont.truetype(font_name, font_size)
        img_with_text = Image.fromarray(frame)
        draw = ImageDraw.Draw(img_with_text)
        [H, W, C] = frame.shape

        use_text_mask = config.get('use_text_mask', False)
        
        # line_width_pixel = config.get('line_width_pixel', 380)
        if dynamic_font_color:
            font_color = self.sample_average_color_in_range(frame)
        else:
            font_color = [155,155,255]
        
        wrap_comments = config.get('wrap_comments', False)
        if wrap_comments:
            line_width_char = config.get('line_width_char', 15)
            comments_wrapped = self.wrap_comments(comments, line_width_char)
        else:
            comments_wrapped = comments

        # n_comments = len(comments_wrapped)
        for comment_idx, comment in enumerate(comments_wrapped):
            # text_raw = "国庆节 / 中秋节 快乐! 国庆节 / 中秋节 快乐!"
            comment_text = comment.content

            # width, height = font.getsize(comment_text)
                
            draw.text(
                xy=(comment.upper_left_x, comment.upper_left_y),  
                text = comment_text, 
                font = font, 
                fill = tuple(font_color + [1]),
                stroke_width=3,
                stroke_fill=(0,0,0,1))
        img_with_text = np.array(img_with_text)
        if use_text_mask:
            # print(img_with_text.max(),frame.max())
            # print(frame.max())
            img_with_text = img_with_text.astype(float)/255 * self.text_mask + (frame.astype(float)/255) * (1-self.text_mask)
            # img_with_text = img_with_text.astype(float)/255 * 0.5 + frame.astype(float)/255 * 0.5
            img_with_text = (img_with_text*255).astype(np.uint8)
            # img_with_text = frame
            # img_with
            pass

        return img_with_text