import io
import re
import configparser
import os


class AssWriter(configparser.ConfigParser):
	def __init__(self):
		configparser.ConfigParser.__init__(self, delimiters=': ')

	def optionxform(self, optionstr):
		return optionstr

	def write(self, fp):
		for section in self._sections:
			self._write_section(fp, section, self._sections[section].items())

	def write_line(self, fp, section_name, section_item):
		fp.write("{}: {}".format(section_item, self[section_name][section_item]))

	def _write_section(self, fp, section_name, section_items):
		fp.write("[{}]\n".format(section_name))
		for key, value in section_items:
			value = self._interpolation.before_write(self, section_name, key, value)
			if value is not None or not self._allow_no_value:
				value = str(value).replace('\n', '\n\t')
			else:
				value = ""
			fp.write("{}: {}\n".format(key, value))

dirname = os.path.dirname(__file__) + '\\'
filename = ['src.srt', 'target.ass']

# Parts of md syntax
match_rules = {'H1': r'#\s+(.*?)\n', 'Emptyline': r'\s*\n', 'Numid': r'\d+', \
	'Srttimemark': r'(\d*:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d*:\d{2}:\d{2}),(\d{3})', \
	'Bold': r'\*\*(.*?)\*\*', 'Italic2': r'\s+_(.*?)_\s+', \
	'Bold2': r'\s+__(.*?)\*\*\s+', 'Italic': r'\*(.*?)\*', \
	'Strikeout': r'~~(.*?)~~', 'Code': r'`(.*?)`',
	'CHN': r'([\u2014\u2026\u3001\u3002\u3007-\u3011\u3014-\u301b\u30fb\u4e00-\u9fa5\uff01-\uff65]+)', \
	'fbk0': r'([\u3400-\u4DBF\u9fa6-\u9ffc\uFA0E\uFA0F\uFA11\uFA13\uFA14\uFA1F\uFA21\uFA23\uFA24\uFA27-\uFA29]+)', \
	'fbk2': r'([\U00020000-\U0002A6DF]+)', \
	'fbk3': r'([\U00030000–\U0003134F]+)'
  }

# ASS Code Effect for text
# Code color -> B7F5F7 as RGB and F7F5B7 as BGR
ass_codes = {
	'Bold': r'{\\b1}\g<1>{\\b0}', 'Italic': r'{\\i1}\g<1>{\\i0}', \
	'Strikeout': r'{\\s1}\g<1>{\\s0}', 'Code': r'{\\fnFira Code}{\\c&HF7F5B7&}\g<1>{\\r}', \
	'CHN': r'{\\fnGlowSansSC Normal Medium}\g<1>{\\r}', \
	'fbk0':r'{\\fnGlowSansSC Normal Medium}\g<1>{\\r}', \
	'fbk2':r'{\\fnGlowSansSC Normal Medium}\g<1>{\\r}', \
	'fbk3':r'{\\fnTH-Tshyn-P1}\g<1>{\\r}'}

# STYLES
plain_style = ['Plain', 'Candara', 14, '&H00FFFFFF', '&H000000FF', '&H66000000', '&HFF000000', \
	0, 0, 0, 0, 100, 100, 0, 0, 3, 1, 0, 2, 5, 5, 10, 1]

# DIALOG_TEMPLATE
dialog_template = ['0', '%s', '%s', '%s', '', '0', '0', '0', '', '%s']


def Write_ass(title: str, styles: list, subtext: list):
	tg = AssWriter()
	tg['Script Info'] = {
		'Title': title,
		'ScriptType': 'v4.00+',
		'Collisions': 'Reverse',
		'WrapStyle': '0',
		'ScaledBorderAndShadow': 'yes',
		'YCbCr Matrix': 'None'
	}
	tg['V4+ Styles'] = {
		'Format': 'Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
		'Style': ','.join(str(token) for token in plain_style)
	}
	tg['Events'] = {
		'Format': 'Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
	}
	with open(dirname + filename[1], 'w', encoding='utf-8') as target_ass:
		tg.write(target_ass)

		tg['Events']['Dialogue'] = ''
		for text in subtext:
			tg.set('Events', 'Dialogue', ','.join(dialog_template) % text)
			tg.write_line(target_ass, 'Events', 'Dialogue')
	
	print('Success.')
	
def Markdown_parse(base: str):
	bold_coded = re.sub(match_rules['Bold'], ass_codes['Bold'], base)
	bold_coded = re.sub(match_rules['Bold2'], ass_codes['Bold'], bold_coded)
	italic_coded = re.sub(match_rules['Italic'], ass_codes['Italic'], bold_coded)
	italic_coded = re.sub(match_rules['Italic2'], ass_codes['Italic'], italic_coded)
	strike_coded = re.sub(match_rules['Strikeout'], ass_codes['Strikeout'], italic_coded)
	syntax_coded = re.sub(match_rules['Code'], ass_codes['Code'], strike_coded)
	gbk_coded = re.sub(match_rules['CHN'], ass_codes['CHN'], syntax_coded)
	fbk0_coded = re.sub(match_rules['fbk0'], ass_codes['fbk0'], gbk_coded)
	fbk2_coded = re.sub(match_rules['fbk2'], ass_codes['fbk2'], fbk0_coded)
	fbk3_coded = re.sub(match_rules['fbk3'], ass_codes['fbk3'], fbk2_coded)
	return fbk3_coded


with open(dirname + filename[0], 'r', encoding='utf-8') as src_md:
	try:
		title = re.match(match_rules['H1'], src_md.readline()).group(1)
	except AttributeError:
		title = 'Mdsub Default Title'
		src_md.seek(0, io.SEEK_SET)
	
	subtext: list = []
	
	for line in src_md:
		if re.match(match_rules['Emptyline'], line):
			dialog_begin = 1
		
		elif re.match(match_rules['Numid'], line) and (dialog_begin == 1):
			dialog_begin = 2
		
		elif re.match(match_rules['Srttimemark'], line) and (dialog_begin == 2):
			matched = re.match(match_rules['Srttimemark'], line)
			st_time = matched.group(1) + '.' + matched.group(2)
			ed_time = matched.group(3) + '.' + matched.group(4)
			if st_time[0] == '0':
				st_time = st_time[1:-1]
			if ed_time[0] == '0':
				ed_time = ed_time[1:-1]
			dialog_begin = 3
			
		elif dialog_begin == 3:		
			subtext.append( (st_time, ed_time, 'Plain', Markdown_parse(line)) )
	
	Write_ass(title, [plain_style], subtext)
