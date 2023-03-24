import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from glob import glob
import os
import json
from copy import deepcopy


filenames=glob(".//0721//NLF_*_01_*.png")
filenames=glob(".//0721//NLF_0721_0730952605_411ECM_N0345120NCAM00709_01_095J02.png")
filenames=glob(".//0678//NLF_0678_0727131066_159ECM_N0320798NCAM08111_01_095J01.png")
filenames=glob("F://3DStuff//3DScans//Mars//rawutils//Perseverance//0736//NLF_0736_0732291806_231ECM_N0370000NCAM00709_01_*.png")

print(len(filenames), "files")





class M20_Image():
    def __init__(self, file):
        self.img = cv.imread(file)
        assert self.img is not None, "file could not be read, check with os.path.exists()"
        # self.filename = (os.path.basename(file))
        try: 
            self.metadata = json.load(open(file[:-4]+"-metadata.json"))
        except:
            raise Exception("necessary json file not available for", file[:-4]+"-metadata.json")
        self.filename = os.path.basename(file)
        self.dirname = os.path.dirname(file)

    #output basic info about loaded image
    def __str__(self):
        return f"{self.filename}, {self.img.shape[0]} x {self.img.shape[1]} pixels, {self.img.shape[2]} band(s), dtype: {self.img.dtype}"
    
    #save image to file
    def save(self, filename=None):
        if filename is None:
            filename = self.dirname + '//testing//' + self.filename
        cv.imwrite(filename, self.img)
        with open(filename[:-4]+"-metadata.json", 'w') as outfile:
            json.dump(self.metadata, outfile, indent=4)


    # unstretch image by analyzing the histogram and closing the gaps
    def unstretch(self):
        histogram = np.histogram(self.img.ravel(),256,[0,256])
        
        # display histogram
        # plt.hist(np.arange(256),256, weights=histogram[0])
        # plt.yscale('log')
        # plt.title(self.filename)
        # plt.show()

        intervals = []
        gaps = []
        lut = np.zeros(256, np.dtype('uint8'))
        previous=0
        for i in range(histogram[0].size):
            if histogram[0][i] == 0:
                intervals.append(i-previous)
                previous=i
                gaps.append(i)
                
            lut[i]=(i-len(intervals))
        
        print(self.filename, "-", len(gaps), "gaps at:", gaps)
        # print(self.filename, lut)
        unstretched = cv.LUT(self.img, lut)
        self.img = unstretched

        histogram_unstretched = np.histogram(self.img.ravel(),256,[0,256])
        
        # display histograms
        fig, ax = plt.subplots(2, sharex=True, sharey=True)
        ax[0].hist(np.arange(256),256, weights=histogram[0])
        ax[0].set_title("raw historgram")
        ax[1].hist(np.arange(256),256, weights=histogram_unstretched[0])
        ax[1].set_title("unstretched histogram")
        ax[0].set_yscale('log')
        fig.suptitle(self.filename)
        # plt.show()

        return


class parsed_filename():
    def __init__(self, filename):
        self.filename = filename
        
        self.instrument =  self.filename[0:2]
        self.filter =  self.filename[2:3]
        self.sol =  self.filename[4:8]
        #capture time
        self.sclk =  self.filename[9:19]
        self.milliseconds =  self.filename[20:23]
        self.product_type =  self.filename[24:26]
        
        self.geometry =  self.filename[26:27]
        self.thumbnail =  self.filename[27:28]
        self.site =  self.filename[28:31]
        self.drive =  self.filename[31:35]
        self.sequence =  self.filename[35:44]
        
        #cam specific options
        self.cam_specific = self.filename[44:48]
        self.zcam_focal_length = self.filename[45:48]
        self.scam_point_number = self.filename[45:48]
        self.pixl_motion_counter = self.filename[44:48]
        self.sherloc_experiment_id = self.filename[44:45]
        self.sherloc_experiment_image_number = self.filename[45:48]
        self.stere0_partner_counter = self.filename[44:45]
        self.video_frame_number = self.filename[45:48]
        self.ECAM_tile = self.filename[45:47]

        self.downsample = self.filename[48:49]
        self.compression = self.filename[49:51]
        self.producer = self.filename[51:52]
        self.version = self.filename[52:54]

    #return full filename when called without addidional arguments
    def __str__(self):
        return self.filename


class ECAM_tile(M20_Image):
    def __init__(self, tilename):
        super().__init__(tilename)
        self.unstretch()
        self.brightness_offset = 0
        try:
            self.scale = int(self.metadata['scale_factor'])
            self.top_left_x = int((int(self.metadata['subframe_rect'][0])-1)/self.scale)
            self.top_left_y = int((int(self.metadata['subframe_rect'][1])-1)/self.scale)
            self.bottom_right_x = int(self.top_left_x + int(self.metadata['subframe_rect'][2])/self.scale)
            self.bottom_right_y = int(self.top_left_y + int(self.metadata['subframe_rect'][3])/self.scale)

            self.border_left = self.top_left_x
            self.border_right = self.bottom_right_x
            self.border_top = self.top_left_y
            self.border_bottom = self.bottom_right_y
            # print([self.top_left_x, self.top_left_y, self.bottom_right_x, self.bottom_right_y, self.scale])
        except:
            raise Exception("necessary json metadata not available")
        
    def __str__(self):
        return f"{self.filename}, {self.img.shape[0]} x {self.img.shape[1]} pixels, {self.img.shape[2]} band(s), dtype: {self.img.dtype}"
        
class ECAM_composite(M20_Image):
    def __init__(self, tilepaths):
        self.tiles = []
        for tilepath in tilepaths:
            self.tiles.append(ECAM_tile(tilepath))
        self.composite_size = self.determine_composite_size(self.tiles)
        self.pad_tiles(self.tiles, self.composite_size)
        self.composite = self.build_composite()

    def determine_composite_size(self, tiles):
        max_x = 0
        max_y = 0
        for tile in tiles:
            if tile.bottom_right_x > max_x:
                max_x = tile.bottom_right_x

            if tile.bottom_right_y > max_y:
                max_y = tile.bottom_right_y
        return [max_y, max_x, 3]
    
    def pad_tiles(self, tiles, composite_size):
        for tile in tiles:
            tile.img = np.pad(tile.img, [[tile.top_left_y, composite_size[0] - tile.bottom_right_y],[tile.top_left_x, composite_size[1] - tile.bottom_right_x],[0,0]], mode='empty')
        return


    def calculate_overlap_box(self, tile1, tile2):
        y_overlap_max = tile1.bottom_right_y
        y_overlap_min = tile2.top_left_y
        x_overlap_min = tile2.top_left_x
        x_overlap_max = tile1.bottom_right_x

        print("borders:",tile1.border_right,tile2.border_left,tile2.border_bottom,tile1.border_top)
        tile1.border_right = int(x_overlap_max - (x_overlap_max-x_overlap_min)/2)
        tile2.border_left = int(x_overlap_min + (x_overlap_max-x_overlap_min)/2)

        tile1.border_bottom = int(y_overlap_max - (y_overlap_max-y_overlap_min)/2)
        tile2.border_top = int(y_overlap_min + (y_overlap_max-y_overlap_min)/2)
        tile1.border_bottom = tile2.bottom_right_y

        print("borders:",tile1.border_right,tile2.border_left,tile2.border_bottom,tile1.border_top)

        overlap_box = [[y_overlap_min+2, y_overlap_max-2], [x_overlap_min+2, x_overlap_max-2]]
        return overlap_box

    def calculate_brightness_offset(self, tile1, tile2, overlap_box):
        tile1_brightness = np.mean(tile1.img[overlap_box[0][0]:overlap_box[0][1], overlap_box[1][0]:overlap_box[1][1]])
        tile2_brightness = np.mean(tile2.img[overlap_box[0][0]:overlap_box[0][1], overlap_box[1][0]:overlap_box[1][1]])
        
        brightness_difference = tile1_brightness + tile1.brightness_offset - tile2_brightness

        tile2.brightness_offset = round(brightness_difference,0)
        print("individual tile/row brightness difference: ", brightness_difference)
        
        return

    def match_brightness(self, tiles):
        row_lines = []
        for tile in tiles:        
            if tile.top_left_y not in row_lines:
                row_lines.append(tile.top_left_y)
        
        rows = [[] for line in row_lines]

        for tile in tiles:
            for i in range(len(row_lines)):
                if tile.top_left_y == row_lines[i]:
                    rows[i].append(tile)
        
        for row in rows:
            for tile in range(len(row)-1):
                y_overlap_min = row[tile].top_left_y
                y_overlap_max = row[tile].bottom_right_y
                x_overlap_min = row[tile+1].top_left_x
                x_overlap_max = row[tile].bottom_right_x

                overlap_box = [[y_overlap_min, y_overlap_max], [x_overlap_min, x_overlap_max]]
                print("row overlap: ", overlap_box)

                self.calculate_brightness_offset(row[tile], row[tile+1], overlap_box)
            
        return self

    def build_composite(self):
        self.composite = np.zeros(self.composite_size, dtype=np.uint8)

        #match brightness and merge tiles
        row_lines = []
        for tile in self.tiles:        
            if tile.top_left_y not in row_lines:
                row_lines.append(tile.top_left_y)
        
        tile_rows = [[] for line in row_lines]
        merged_rows = []
        merged_composite = []

        for tile in self.tiles:
            for i, line in enumerate(row_lines):
                if tile.top_left_y == row_lines[i]:
                    tile_rows[i].append(tile)
        

        for row_index, row in enumerate(tile_rows):
            
            #calculate brightness offsets for tiles in row
            for tile_index, tile in enumerate(row[:-1]):
                overlap_box = self.calculate_overlap_box(row[tile_index], row[tile_index+1])
                print("tile overlap: ", overlap_box)

                self.calculate_brightness_offset(row[tile_index], row[tile_index+1], overlap_box)

            
            
            #merge adjusted tiles into new row
            merged_rows.append(deepcopy(row[0]))
            print("copied tile extent: ",[[merged_rows[row_index].top_left_y,merged_rows[row_index].bottom_right_y],[merged_rows[row_index].top_left_x,merged_rows[row_index].bottom_right_x]])

            min_offset = 0
            for tile_index, tile in enumerate(row):
                
                if tile.brightness_offset < min_offset:
                    min_offset = tile.brightness_offset

            for tile_index, tile in enumerate(row):    
                print("working on tile: ", tile_index)
                print("working on row: ", row_index)
                print("min brightness difference tiles: ", min_offset)
                tile.img += np.uint8(tile.brightness_offset - min_offset)
                # merged_rows[row_index].img[tile.top_left_y:tile.bottom_right_y, tile.top_left_x+8:tile.bottom_right_x-8] = tile.img[tile.top_left_y:tile.bottom_right_y, tile.top_left_x+8:tile.bottom_right_x-8]
                merged_rows[row_index].img[tile.top_left_y:tile.bottom_right_y, tile.border_left:tile.border_right] = tile.img[tile.top_left_y:tile.bottom_right_y, tile.border_left:tile.border_right]
                print("merging tile at", [[tile.top_left_y,tile.bottom_right_y],[tile.border_left,tile.border_right]])

                #set new extents for row
                if tile.top_left_y < merged_rows[row_index].top_left_y:
                    merged_rows[row_index].top_left_y = tile.top_left_y
                if tile.bottom_right_y > merged_rows[row_index].bottom_right_y:
                    merged_rows[row_index].bottom_right_y = tile.bottom_right_y
                if tile.top_left_x < merged_rows[row_index].top_left_x:
                    merged_rows[row_index].top_left_x = tile.top_left_x
                if tile.bottom_right_x > merged_rows[row_index].bottom_right_x:
                    merged_rows[row_index].bottom_right_x = tile.bottom_right_x

            print("merged row extent: ",[[merged_rows[row_index].top_left_y,merged_rows[row_index].bottom_right_y],[merged_rows[row_index].top_left_x,merged_rows[row_index].bottom_right_x]])

        for row_index, merged_row in enumerate(merged_rows[:-1]):

            overlap_box = self.calculate_overlap_box(merged_rows[row_index], merged_rows[row_index+1])
            print("merged rows overlap: ", overlap_box)

            self.calculate_brightness_offset(merged_rows[row_index], merged_rows[row_index+1], overlap_box)


            
        #merge adjusted rows into full composite
        merged_composite = deepcopy(merged_rows[0])
        merged_composite.brightness_offset = 0

        
        min_offset = 0
        for row_index, merged_row in enumerate(merged_rows):
            
            if merged_row.brightness_offset < min_offset:
                min_offset = merged_row.brightness_offset
            print("min brightness difference rows: ", min_offset)
            
        for row_index, merged_row in enumerate(merged_rows):
            merged_row.img += np.uint8(merged_row.brightness_offset - min_offset)
            # merged_composite.img[merged_row.top_left_y+8:merged_row.bottom_right_y-8, merged_row.top_left_x:merged_row.bottom_right_x] = merged_row.img[merged_row.top_left_y+8:merged_row.bottom_right_y-8, merged_row.top_left_x:merged_row.bottom_right_x]
            merged_composite.img[merged_row.border_top:merged_row.border_bottom, merged_row.top_left_x:merged_row.bottom_right_x] = merged_row.img[merged_row.border_top:merged_row.border_bottom, merged_row.top_left_x:merged_row.bottom_right_x]
            print("merging row at", [[merged_row.border_top,merged_row.border_bottom], [merged_row.top_left_x,merged_row.bottom_right_x]])
            
            
            #set new extents for composite
            if merged_row.top_left_y < merged_composite.top_left_y:
                merged_composite.top_left_y = merged_row.top_left_y
            if merged_row.bottom_right_y > merged_composite.bottom_right_y:
                merged_composite.bottom_right_y = merged_row.bottom_right_y
            if merged_row.top_left_x < merged_composite.top_left_x:
                merged_composite.top_left_x = merged_row.top_left_x
            if merged_row.bottom_right_x > merged_composite.bottom_right_x:
                merged_composite.bottom_right_x = merged_row.bottom_right_x

            print("merged composite extent: ",[[merged_composite.top_left_y,merged_composite.bottom_right_y],[merged_composite.top_left_x,merged_composite.bottom_right_x]])

        # if merged_composite.filename.downsample == "0":
        #     print("redebayering with VNG to remove zipper artefacts")
        #     merged_composite.redebayer()  

        return merged_composite
    
def main(input_pattern):

    filenames = glob(input_pattern)
    
    sclk = []

    for file in filenames:
        ##check if os.path.basename(file)[10:19] is in sclk, if not append it
        if os.path.basename(file)[10:19] not in sclk:
            sclk.append(os.path.basename(file)[10:19])
            
            tilepaths = glob(os.path.dirname(file) + "//" + "NLF*" + os.path.basename(file)[10:19] + "*J0?.png")
            composite = ECAM_composite(tilepaths).composite
            print(composite.filename)
            composite.save()


            
    print(sclk)


main("F:/3DStuff/3DScans/Mars/tools/0718/NLF*.png")