import logging
import os

class Logger():
    def set_up_logger(self, py_log_path, py_log_name):
        # set up logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

        # py_log = os.path.join(py_log_path,'conversion_test.log')
        py_log = os.path.join(py_log_path, py_log_name)
        # py_log = os.path.join(py_log_path,'TDF_zip_transfer_log.log')
        file_handler = logging.FileHandler(py_log)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        # stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        return logger

class CreateFolder():
    """
    class to create a new folder given a filepath
    """
    def create_folder(self, dir):
        """
        Create the directory if not exists.

        :param dir: str
            directory to create
        """
        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except Exception:
                print("Error! Could not create directory " + dir)
