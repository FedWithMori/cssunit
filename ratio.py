import sublime
import sublime_plugin
import re
import time
import os

SETTINGS = {}
lastCompletion = {"needFix": False, "value": None, "region": None}

# 调用init_settings方法
def plugin_loaded():
    init_settings()

# 初始化设置，加载cssrem.sublime-settings文件
def init_settings():
    get_settings()
    sublime.load_settings('ratio.sublime-settings').add_on_change('get_settings', get_settings)

# 加载settings文件，设置相关属性
def get_settings():
    settings = sublime.load_settings('ratio.sublime-settings')
    SETTINGS['unit'] = settings.get('unit', ' * @ratio')
    SETTINGS['available_file_types'] = settings.get('available_file_types', ['.css', '.less', '.sass'])

def get_setting(view, key):
    return view.settings().get(key, SETTINGS[key]);

# 定义一个类
class CssRatioCommand(sublime_plugin.EventListener):
    def on_text_command(self, view, name, args):
        if name == 'commit_completion':
           # 运行replace_rem命令
           view.run_command('replace_rem') 
        return None

    def on_query_completions(self, view, prefix, locations):
        # print('cssrem start {0}, {1}'.format(prefix, locations))

        # only works on specific file types  判断目标文件类型
        fileName, fileExtension = os.path.splitext(view.file_name())
        if not fileExtension.lower() in get_setting(view, 'available_file_types'):
            return []

        # reset completion match
        lastCompletion["needFix"] = False
        location = locations[0]
        snippets = []

        # get rem match 
        # re.compile => 将正则表达式编译成一个正则表达式对象  捕获符合类似120px规则的字符
        match = re.compile("([\d.]+)p(x)?").match(prefix)
        if match:
            lineLocation = view.line(location)
            line = view.substr(sublime.Region(lineLocation.a, location))
            value = match.group(1)
            
            # fix: values like `0.5px`
            segmentStart = line.rfind(" ", 0, location)
            if segmentStart == -1:
                segmentStart = 0
            segmentStr = line[segmentStart:location]

            segment = re.compile("([\d.])+" + value).search(segmentStr)
            if segment:
                value = segment.group(0)
                start = lineLocation.a + segmentStart + 0 + segment.start(0)
                lastCompletion["needFix"] = True
            else:
                start = location

            # remValue = round(float(value) / get_setting(view, 'px_to_rem'), get_setting(view, 'max_rem_fraction_length'))

            # save them for replace fix
            lastCompletion["value"] = value + get_setting(view, 'unit')
            lastCompletion["region"] = sublime.Region(start, location)

            # set completion snippet
            snippets += [(value + 'px ->' + value + get_setting(view, 'unit'), value + get_setting(view, 'unit'))]

        # print("cssrem: {0}".format(snippets))
        return snippets

class ReplaceRatioCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        needFix = lastCompletion["needFix"]
        if needFix == True:
            value = lastCompletion["value"]
            region = lastCompletion["region"]
            # print('replace: {0}, {1}'.format(value, region))
            self.view.replace(edit, region, value)
            self.view.end_edit(edit)