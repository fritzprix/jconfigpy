
FILE_ERROR_FORMAT = '{0} doesn\'t exists'


class FileNotExistError(BaseException):
    def __init__(self, filename):
        self.message = FILE_ERROR_FORMAT.format(filename)
        BaseException.__init__(self)

    def __str__(self):
        return self.message
