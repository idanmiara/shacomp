import fnmatch

from shacomp.old import helper

base_path = r'd:\dev\shacomp'
path = base_path + r'\**\*.*'
output_root = r'd:\dev\temp'
# whitelist = ['*.py', '*.bat']
# blacklist = ['__*']
# white_pattern = fnmatch.translate('*.py')
black_pattern = fnmatch.translate('*.txt')

output_filename = helper.make_signaturs(path, base_path, output_root, use_cache=False, white_pattern=None, black_pattern=black_pattern)
helper.verify_signatures(output_filename, base_path, output_root, write_ok_files_log=True, verify_sha=True)
