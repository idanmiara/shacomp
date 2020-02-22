import os
import shacomp.helper as hlp

if __name__ == "__main__":
    pattern = r'**\*'
    # path = 'p:\\'
    base_path = 'p:\\'
    path = r'p:'
    # path = r'p:\0\Pictures5'
    # path = r'd:\dev\shacomp'
    input_path = os.path.join(path, pattern)
    output_root = r'd:\dev\shacomp\temp'
    hlp.make_signatures(input_path, base_path, output_root)
