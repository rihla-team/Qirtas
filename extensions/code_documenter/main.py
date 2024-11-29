from utils.code_documenter import CodeDocumenter, InteractiveDocViewer


class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.documenter = CodeDocumenter(editor)
        self.viewer = None
        
    def get_menu_items(self):
        return [
            {
                'name': 'الدليل التفاعلي للمطورين',
                'callback': self.show_docs
            }
        ]
        
    def show_docs(self):
        if not self.viewer:
            self.viewer = InteractiveDocViewer(self.documenter, self.editor)
        self.viewer.show()  