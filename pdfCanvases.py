from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import inch


#PDF Classes
class NumberedPageCanvas8x11(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            super().showPage()
        super().save()
    def draw_page_number(self, page_count):
        page = "Page %s of %s" % (self._pageNumber, page_count)
        self.setFont("Helvetica", 8)
        self.drawRightString(8.25 * inch, 0.22 * inch, page)

class NumberedPageCanvas11x8(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            super().showPage()
        super().save()
    def draw_page_number(self, page_count):
        page = "Page %s of %s" % (self._pageNumber, page_count)
        self.setFont("Helvetica", 8)
        self.drawRightString(10.75 * inch, 0.22 * inch, page)

class NumberedPageCanvas17x11(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            super().showPage()
        super().save()
    def draw_page_number(self, page_count):
        page = "Page %s of %s" % (self._pageNumber, page_count)
        self.setFont("Helvetica", 8)
        self.drawRightString(16.75 * inch, 0.22 * inch, page)