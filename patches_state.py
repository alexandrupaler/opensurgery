"""
 Keeping track of the X/Z orientation in this class
"""

from enum import Enum


class XOrientation(Enum):
    ORIGINAL = 1
    ROTATED = 3


class PatchesState:
    def __init__(self):
        print("Patches State")

        self.the_active_patches = []

        self.per_patch_x_orientation = {}

    def add_active_patch(self, patch, x_orientation=XOrientation.ORIGINAL):
        self.the_active_patches.append(patch)
        self.per_patch_x_orientation[patch] = x_orientation

    def remove_active_patch(self, patch):
        # remove the patch from being tracked
        self.the_active_patches.remove(patch)

        # remove the stored orientation
        del self.per_patch_x_orientation[patch]

    def is_patch_active(self, patch):
        # if it is in the active ones?
        return patch in self.the_active_patches

    def get_all_active_patches(self):
        return self.the_active_patches

    def rotate_patch(self, patch):
        if self.is_patch_active(patch):
            c_orient = self.per_patch_x_orientation[patch]
            if c_orient == XOrientation.ORIGINAL:
                self.per_patch_x_orientation[patch] = XOrientation.ROTATED
            else:
                self.per_patch_x_orientation[patch] = XOrientation.ORIGINAL
        else:
            print("ERROR! Patch is not active " + str(patch))

    """
        The number is a sum of two powers of two
        Which stand for the bits from the 6 available of a cube
        This number is used by the Javascript to draw the X faces
        
        // build each side of the box geometry
        //ORIGINAL is 1 + 2
        if((which_faces & 1) == 1)
            this.buildPlane(poss, 'z', 'y', 'x', - 1, - 1, depth, height, width); // px
        if((which_faces & 2) == 2)
            this.buildPlane(poss, 'z', 'y', 'x', 1, - 1, depth, height, - width); // nx
        
        //ROTATED 4 + 8
        if((which_faces & 4) == 4)
            this.buildPlane(poss, 'x', 'z', 'y', 1, 1, width, depth, height); // py
        if((which_faces & 8) == 8)
            this.buildPlane(poss, 'x', 'z', 'y', 1, - 1, width, depth, - height); // ny
        
        //pz and nz are not important for lattice surgery, because these are along the time axis
        if((which_faces & 16) == 16)
            this.buildPlane(poss, 'x', 'y', 'z', 1, - 1, width, height, depth); // pz
        if((which_faces & 32) == 32)
            this.buildPlane(poss, 'x', 'y', 'z', - 1, - 1, width, height, - depth); // nz
    }
    """

    def get_patch_orientation_as_number(self, patch):
        if self.is_patch_active(patch):
            c_orient = self.per_patch_x_orientation[patch]
            if c_orient == XOrientation.ORIGINAL:
                return (63 - 3)  # 1 + 2
            else:
                return (63 - 12)  # 4 + 8
        else:
            print("ERROR! Patch is not active! " + str(patch))

        # HORROR
        return -1
