import untangle


class AiFileReader:
    def __init__(self, xml_ai_data: str):
        if not untangle.is_url(xml_ai_data):
            # print("error xml file not found")
            pass  # it might be found anyway - this is a bug in untangle

        self.xml_parser = untangle.parse(xml_ai_data)  # if it is really not found, this fails

    def has_ai_data(self, name):
        for elem in self.xml_parser.AI.get_elements():
            if elem.get_attribute('name') == name:
                return True
        return False

    def get_characteristics(self, char_dict, name):
        for elem in self.xml_parser.AI.children:
            if elem.get_attribute('name') == name:
                for child in elem.characteristics.children:
                    print(child._name)
