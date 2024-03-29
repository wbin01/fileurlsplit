#!/usr/bin/env python3
import os
import re
import string
import sys
import urllib.parse


class Error(Exception):
    """Exception base class"""
    pass


class FilenameTooLongError(Error):
    """Raised when the filename (with extension) is too long.
    Usually longer than 255 characters.
    """
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.__message = message

    @property
    def message(self) -> str:
        """Error message"""
        return self.__message


class AbsolutePathError(Error):
    """Raised when a passed URL doesn't have an absolute path
    prefix like a slash "/" or "file://".
    """
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.__message = message

    @property
    def message(self) -> str:
        """Error message"""
        return self.__message


class InvalidCharacterError(Error):
    """Raised when the string contains a character not allowed
    for the desired action.
    """
    def __init__(
            self,
            message: str,
            invalid_character_found: str,
            all_invalid_characters_list: list) -> None:
        super().__init__(message)
        self.__message = message
        self.__invalid_character_found = invalid_character_found
        self.__all_invalid_characters_list = all_invalid_characters_list

    @property
    def message(self) -> str:
        """Error message"""
        return self.__message

    @property
    def invalid_character_found(self) -> str:
        """The invalid character found"""
        return self.__invalid_character_found

    @property
    def all_invalid_characters_list(self) -> list:
        """The all invalid characters list"""
        return self.__all_invalid_characters_list


class InvalidFilenameError(Error):
    """
    when the name is reserved for the exclusive use of the operating system.
    """
    def __init__(self, message: str, all_invalid_filename_list: list) -> None:
        super().__init__(message)
        self.__message = message
        self.__all_invalid_filename_list = all_invalid_filename_list

    @property
    def message(self) -> str:
        """Error message"""
        return self.__message

    @property
    def all_invalid_filename_list(self) -> list:
        """The all invalid filename list"""
        return self.__all_invalid_filename_list


class FileUrlSplit(object):
    """Object that handles file url divisions

    From the file you can get the full url, extension, name or path.

    >>> file_url_split = FileUrlSplit(file_url='file:///home/user/photo.png')

    >>> print(file_url_split)
    FileUrlSplit("/home/user/photo.png")

    Get url
    >>> file_url_split.url
    '/home/user/photo.png'

    Get only file path
    >>> file_url_split.path
    '/home/user/'

    Get only file name without the extension
    >>> file_url_split.name
    'photo'

    Get filename with the extension
    >>> file_url_split.filename
    'photo.png'

    Get file extension
    >>> file_url_split.extension
    '.png'
    """
    __platform = None
    __invalid_chars = None
    __invalid_names = None

    def __init__(self, file_url: str = None) -> None:
        """Constructor

        It will not be checked if the file from the passed URL already exists.
        The goal is just to split the string.

        The URL must be absolute or an exception will be raised. This means
        that the string must start with a valid path prefix. Example: '/path',
        'c:/path', 'file:///path'.

        If the URL contains backslashes '\', then it must be escaped or passed
        as a raw string. Example: r'C:\path', 'c:\\path'

        :param file_url: URL string
        """
        self.__set_invalid_chars()
        self.__url = self.__get_url(file_url)
        self.__path = self.__get_path()
        self.__filename = self.__get_filename()
        self.__extension = self.__get_extension()
        self.__name = self.__get_name()

    @property
    def url(self) -> str:
        """Get the clean url

        URL without the file prefix, such as "file://".

        :return: File url
        """
        return self.__url

    @url.setter
    def url(self, file_url: str) -> None:
        """Set up a new URL

        A new URL can change all other properties.
        The URL must be absolute or an exception will be raised.
        This means that the string must start with a valid path prefix.
        Example: '/path', 'c:/path', 'file:///path'.

        :param file_url: New URL string
        :raises AbsolutePathError: When URL passed is not absolute
        :raises InvalidCharacterError: If URL passed contains reserved chars
        :raises FilenameTooLongError: File name with the extension is too long
        """
        if file_url != self.__url:
            # Clean path: AbsolutePathError
            file_url = self.__get_url(file_url=file_url)

            # Valid URL chars: InvalidCharacterError
            for split_name in file_url.split('/'):
                # Invalid chars in dirs
                self.__check_invalid_chars(str_to_check=split_name)

                # Invalid dir name: InvalidCharacterError
                self.__check_invalid_names(name_string=split_name)

                # Valid len size
                if len(split_name) > 255:
                    raise FilenameTooLongError(
                        message=(
                            'File name too long. The file name together with '
                            'the extension cannot exceed the limit of 255 '
                            'characters.'))

            # Update URL
            self.__url = self.__get_url(file_url)

            # Update the affected properties
            self.__path = self.__get_path()
            self.__filename = self.__get_filename()  # FilenameTooLongError
            self.__extension = self.__get_extension()  # FilenameTooLongError
            self.__name = self.__get_name()  # FilenameTooLongError

    @property
    def path(self) -> str:
        """Get file path only

        The path without the file name and extension.

        :return: File path
        """
        return self.__path

    @path.setter
    def path(self, file_path: str) -> None:
        """Set a new path to the file

        The path must have absolute URL or an exception will be raised.
        This means that the string must start with a valid path prefix.
        Example: '/path', 'c:/path', 'file:///path'.
        This also updates the 'url' propertie.

        :param file_path: New path URL string
        :raises AbsolutePathError: When path passed is not absolute
        :raises InvalidCharacterError: If path passed contains reserved chars
        """
        # Clean path: AbsolutePathError
        file_path = self.__get_url(file_url=file_path)

        if file_path != self.__path:
            if file_path[-1] != '/':
                file_path = file_path + '/'

            # Valid path chars: InvalidCharacterError
            for split_name in file_path.split('/'):
                # Invalid chars in dirs
                self.__check_invalid_chars(str_to_check=split_name)

                # Invalid dir name: InvalidCharacterError
                self.__check_invalid_names(name_string=split_name)

                # Valid len size
                if len(split_name) > 255:
                    raise FilenameTooLongError(
                        message=(
                            'File name too long. The file name together with '
                            'the extension cannot exceed the limit of 255 '
                            'characters.'))

            # Update path
            self.__path = file_path

            # Update the affected properties
            self.__url = self.__get_url(file_path + self.__filename)

    @property
    def name(self) -> str:
        """Get only the file name

        File name without the extension and without the path.

        :return: File name
        """
        return self.__name

    @name.setter
    def name(self, file_name: str) -> None:
        """Set a new name for the file

        This also updates the 'url' and 'filename' properties.
        The extension doesn't change, so just pass the filename without the
        extension.
        If you want to pass a name along with the extension and change
        everything at once, use the "filename" property of this class.
        If you only want to change the file extension, use the "extension"
        property.

        :param file_name: String containing the file name
        :raises InvalidCharacterError: If name passed contains reserved chars
        :raises FilenameTooLongError: File name with the extension is too long
        """
        # None | UrlEncode
        file_name = '' if not file_name else urllib.parse.unquote(
            string=file_name, encoding='utf-8', errors='replace')

        if file_name != self.__name:
            if file_name:
                # Valid chars in file name: InvalidCharacterError
                self.__check_invalid_chars(str_to_check=file_name)

                # Valid file name: InvalidCharacterError
                self.__check_invalid_names(
                    name_string=file_name + self.__extension)

                # Valid len size
                if len(file_name + self.__extension) > 255:
                    raise FilenameTooLongError(
                        message=(
                            'File name too long. The file name together with '
                            'the extension cannot exceed the limit of 255 '
                            'characters.'))

                self.__name = file_name
                self.__filename = self.__name + self.__extension
                self.__url = self.__path + self.__filename

            else:
                self.__name = self.__extension
                self.__filename = self.__extension
                self.__url = self.__path + self.__extension
                self.__extension = ''

    @property
    def filename(self) -> str:
        """Get only the filename

        Filename with the extension but without the path.

        :return: Filename
        """
        return self.__filename

    @filename.setter
    def filename(self, filename: str) -> None:
        """Set a new filename for the file

        This also updates the 'url', 'name' and 'extension' properties.
        It must contain the file extension, such as "foo.txt". If you don't
        pass the name along with the extension, then the existing extension
        will be removed.
        If you want to change the name of the file without changing the
        existing extension, use the "name" property of this class.

        :param filename: String containing the filename
        :raises InvalidCharacterError: If name passed contains reserved chars
        :raises FilenameTooLongError: File name with the extension is too long
        """
        # None | UrlEncode
        filename = '' if not filename else urllib.parse.unquote(
            string=filename, encoding='utf-8', errors='replace')

        if filename != self.__filename:
            if filename:
                # Valid chars in filename: InvalidCharacterError
                self.__check_invalid_chars(str_to_check=filename)

                # Valid filename: InvalidCharacterError
                self.__check_invalid_names(name_string=filename)

                # Valid len size
                if len(filename) > 255:
                    raise FilenameTooLongError(
                        message=(
                            'Filename too long. The file name together with '
                            'the extension cannot exceed the limit of 255 '
                            'characters.'))

            self.__filename = filename
            self.__url = self.__path + self.__filename
            self.__extension = self.__get_extension()
            self.__name = self.__get_name()

    @property
    def extension(self) -> str:
        """Get file extension only

        Only the file extension without the name and path.

        :return: File extension
        """
        return self.__extension

    @extension.setter
    def extension(self, file_extension: str) -> None:
        """Set a new extension for the file

        This also updates the 'url', and 'filename'properties.

        :param file_extension: String containing the filename extension
        :raises InvalidCharacterError: If name passed contains reserved chars
        :raises FilenameTooLongError: File name with the extension is too long
        """
        # None | UrlEncode
        file_extension = '' if not file_extension else urllib.parse.unquote(
            string=file_extension, encoding='utf-8', errors='replace')

        if file_extension != self.__extension:
            if file_extension:
                # Valid extension chars: InvalidCharacterError
                self.__check_invalid_chars(str_to_check=file_extension)

                # Fix dot
                if file_extension[0] != '.':
                    file_extension = '.' + file_extension

                # Valid len size
                if len(self.__name + file_extension) > 255:
                    raise FilenameTooLongError(
                        message=(
                            'File extension too long. The file name together '
                            'with the extension cannot exceed the limit of '
                            '255 characters.'))

            self.__extension = file_extension
            self.__url = self.__path + self.__name + self.__extension
            self.__filename = self.__get_filename()

    @staticmethod
    def __get_url(file_url: str) -> str:
        # Returns a clean url
        # Decode url-encode and remove prefix like "file://", "c:/"
        # raise: AbsolutePathError

        # Empt
        if not file_url:
            return '/'

        # Decode url
        file_url = urllib.parse.unquote(
            string=file_url, encoding='utf-8', errors='replace')

        # Fix slash
        file_url = file_url.replace('\\', '/')

        # Raise a non-absolute path
        absolute_path_error_msg = (
            'You need an absolute URL like: '
            '"/path", "file://path", "file:///path" or "c:/path"')

        prefix_match = re.search(r'^\w+:', file_url)  # file prefix -> c: file:
        if prefix_match:
            if file_url[prefix_match.end():][0] != '/':
                raise AbsolutePathError(message=absolute_path_error_msg)
        else:
            if file_url[0] != '/':
                raise AbsolutePathError(message=absolute_path_error_msg)

        # Match - remove prefix like "file://", "c:/"
        match = re.search(r'/\w.+$', file_url)
        if match:
            file_url = file_url[match.start():match.end()]

        return file_url

    def __get_path(self) -> str:
        # Returns only the file path
        path = os.path.dirname(self.__url)
        return path if path == '/' else path + '/'

    def __get_filename(self) -> str:
        # Returns the filename with the extension
        return self.__url.replace(self.__path, '')

    def __get_extension(self) -> str:
        # Returns only the file extension

        # splitext does not work for .tar*
        # >>> filename, file_extension = os.path.splitext("/path/foo.tar.gz")
        # >>> file_extension
        # '.gz'

        # Olhar o fim do nome do arquivo a partir do último ponto, não produz
        # o resultado esperado, pois um arquivo de nome '.txt' não pode ser
        # reconhecido como um arquivo de nome vazio '' e extensão '.txt', e
        # sim como um arquivo que tem o nome oculto '.txt' e extensão vazia ''.
        # Remover o ponto '.' no início do nome do arquivo, ajuda na posterior
        # divisão ( split('.') ). Na extensão nada é alterado.
        file_name = self.__filename.lstrip('.')

        # Arquivos sem extensão
        if '.' not in file_name or file_name[-1] == '.':
            return ''

        # Divide o nome do arquivo em todos os pontos, criando uma lista.
        # O último item, representam a extensão.
        file_slices = file_name.split('.')

        # Pontos no início e fim ja foram tratados, então uma lista de 2 itens
        # representa um arquivo que só tem uma extensão.
        # O primeiro item é o nome do arquivo, e último item é a extensão.
        if len(file_slices) == 2:
            return '.' + file_slices[-1]

        # Lista sempre de 3 itens pra cima, representa arquivo que
        # tem mais de uma extensão, ou pontos no meio do nome.
        elif len(file_slices) > 2:

            # Extensão interna. Futuramente, adicionar extensões internas aqui.
            if file_slices[-2] == 'tar':
                return '.' + file_slices[-2] + '.' + file_slices[-1]

            return '.' + file_slices[-1]

    def __get_name(self) -> str:
        # Returns the file name without the extension
        return self.__filename.replace(self.__extension, '')

    def __set_invalid_chars(self) -> None:
        # Linux:             linux or linux2 (*)
        # Windows:           win32
        # Windows/Cygwin:    cygwin
        # Windows/MSYS2:     msys
        # Mac OS X:          darwin
        # OS/2:              os2
        # OS/2 EMX:          os2emx
        # RiscOS:            riscos
        # AtheOS:            atheos
        # FreeBSD 7:         freebsd7
        # FreeBSD 8:         freebsd8
        # FreeBSD N:         freebsdN
        # OpenBSD 6:         openbsd6

        if not self.__platform:
            if sys.platform.startswith('linux'):
                self.__platform = 'Linux'
                self.__invalid_chars = ['/', '\\']  # Linux

            elif 'bsd' in sys.platform:
                self.__platform = 'BSD'
                self.__invalid_chars = ['/', '\\', ':']

            elif sys.platform == 'darwin':
                self.__platform = 'Mac'
                self.__invalid_chars = ['/', '\\', ':']

            elif 'win' in sys.platform or 'msys' in sys.platform:
                self.__platform = 'Windows'
                self.__invalid_chars = [
                    '\\', '/', ':', '*', '?', '"', '<', '>', '|']
                self.__invalid_names = [
                    'CON', 'PRN', 'AUX', 'NUL', 'COM0', 'COM1', 'COM2', 'COM3',
                    'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT0',
                    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7',
                    'LPT8', 'LPT9']
            else:
                self.__platform = 'Another'
                self.__invalid_chars = [
                    x for x in string.punctuation
                    if x not in ['~', ' ', '-', '_', '.']]

    def __check_invalid_chars(self, str_to_check: str) -> None:
        # raise: InvalidCharacterError
        for invalid_char in self.__invalid_chars:
            if invalid_char in str_to_check:
                raise InvalidCharacterError(
                    message=f"Cannot contain '{invalid_char}'",
                    invalid_character_found=invalid_char,
                    all_invalid_characters_list=self.__invalid_chars,
                )

    def __check_invalid_names(self, name_string: str) -> None:
        if self.__invalid_names:
            if name_string in self.__invalid_names:
                raise InvalidFilenameError(
                    message=(f'The name "{name_string}" is reserved and '
                             'cannot be used.'),
                    all_invalid_filename_list=self.__invalid_names,
                )

    def __repr__(self):
        return f'FileUrlSplit("{self.__url}")'


if __name__ == "__main__":
    # No third-party testing coverage
    import doctest     # pragma: no cover
    doctest.testmod()  # pragma: no cover
