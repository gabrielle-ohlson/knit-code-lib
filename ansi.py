# @staticmethod 
class Ansi:
	reset = "\u001b[0m"
	#
	bold = "\u001b[1m"
	italic = "\u001b[3m"
	underline = "\u001b[4m"
	invert = "\u001b[7m" #reversed
	strike = "\u001b[9m"
	#
	black = "\u001b[30m"
	red = "\u001b[31m"
	green = "\u001b[32m"
	yellow = "\u001b[33m"
	blue = "\u001b[34m"
	magenta = "\u001b[35m"
	cyan = "\u001b[36m"
	white = "\u001b[37m"
	#
	class Bright:
		black = "\u001b[30;1m"
		red = "\u001b[31;1m"
		green = "\u001b[32;1m"
		yellow = "\u001b[33;1m"
		blue = "\u001b[34;1m"
		magenta = "\u001b[35;1m"
		cyan = "\u001b[36;1m"
		white = "\u001b[37;1m"
	
	class Background:
		black = "\u001b[40m"
		red = "\u001b[41m"
		green = "\u001b[42m"
		yellow = "\u001b[43m"
		blue = "\u001b[44m"
		magenta = "\u001b[45m"
		cyan = "\u001b[46m"
		white = "\u001b[47m"

		class Bright:
			black = "\u001b[40;1m"
			red = "\u001b[41;1m"
			green = "\u001b[42;1m"
			yellow = "\u001b[43;1m"
			blue = "\u001b[44;1m"
			magenta = "\u001b[45;1m"
			cyan = "\u001b[46;1m"
			white = "\u001b[47;1m"



def fmt(text, *ansi_escape_codes):
	res = ""
	for code in ansi_escape_codes:
		res += code
	#
	res += text + Ansi.reset
	#
	return res


# print(fmt("Hello", Ansi.underline, Ansi.magenta, Ansi.Background.Bright.yellow) + fmt(" how are", Ansi.Bright.cyan, Ansi.italic) + " you?")


# game_id = "141776535"
# note = "fun group of cards (should def play with Yoni), but regret not getting a 'Torturer' earlier (also, focused too much on getting rid of Coppers with 'Sauna' + Silver in response to 'Cutthroat')"

# print(f"\nparsing {fmt('game #'+game_id, Ansi.bold, Ansi.green)}" + ' - with note: "' + fmt(note, Ansi.italic) + '"' if len(note.strip()) else '' + "\n")


# print(f"\nparsing {fmt('game #'+game_id, Ansi.bold, Ansi.green)}" + fmt(' - with note: "'+note+'"', Ansi.italic) if len(note.strip()) else '' + "\n")

# # print(f"\nparsing {fmt('game #'+game_id, Ansi.bold, Ansi.Bright.green)}{fmt(' (with note '+note+')', Ansi.italic) if len(note.strip()) else ''}\n")

# name = "Test"
# print(f"Hello, \"{name}\"")

