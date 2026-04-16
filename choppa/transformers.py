import xml.etree.ElementTree as ET
from typing import Dict, Optional, Any

class Srx1Transformer:
    def transform(self, srx1_xml: str, parameter_map: Optional[Dict[str, Any]] = None) -> str:
        if parameter_map is None:
            parameter_map = {}
        
        map_rule_name = parameter_map.get("map_rule_name")
        
        root_1 = ET.fromstring(srx1_xml)
        
        root_2 = ET.Element("srx")
        root_2.set("version", "2.0")
        root_2.set("xmlns", "http://www.lisa.org/srx20")
        root_2.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root_2.set("xsi:schemaLocation", "http://www.lisa.org/srx20 srx20.xsd")
        
        header_1 = root_1.find("header")
        header_2 = ET.SubElement(root_2, "header")
        if header_1 is not None:
            for attr, value in header_1.attrib.items():
                header_2.set(attr, value)
        header_2.set("cascade", "no")
        
        if header_1 is not None:
            for formathandle in header_1.findall("formathandle"):
                fh_2 = ET.SubElement(header_2, "formathandle")
                for attr, value in formathandle.attrib.items():
                    fh_2.set(attr, value)
        
        body_1 = root_1.find("body")
        if body_1 is not None:
            body_2 = ET.SubElement(root_2, "body")
            
            lr_1_root = body_1.find("languagerules")
            if lr_1_root is not None:
                lr_2_root = ET.SubElement(body_2, "languagerules")
                for lr_1 in lr_1_root.findall("languagerule"):
                    lr_2 = ET.SubElement(lr_2_root, "languagerule")
                    for attr, value in lr_1.attrib.items():
                        lr_2.set(attr, value)
                    
                    for rule_1 in lr_1.findall("rule"):
                        rule_2 = ET.SubElement(lr_2, "rule")
                        for attr, value in rule_1.attrib.items():
                            rule_2.set(attr, value)
                        
                        before = rule_1.find("beforebreak")
                        if before is not None and before.text:
                            ET.SubElement(rule_2, "beforebreak").text = before.text
                        
                        after = rule_1.find("afterbreak")
                        if after is not None and after.text:
                            ET.SubElement(rule_2, "afterbreak").text = after.text
            
            mr_1_root = body_1.find("maprules")
            if mr_1_root is not None:
                mr_2_root = ET.SubElement(body_2, "maprules")
                
                selected_mr_1 = None
                if map_rule_name:
                    for mr_1 in mr_1_root.findall("maprule"):
                        if mr_1.get("maprulename") == map_rule_name:
                            selected_mr_1 = mr_1
                            break
                    if selected_mr_1 is None:
                        raise ValueError(f"Map rule '{map_rule_name}' not found.")
                else:
                    selected_mr_1 = mr_1_root.find("maprule")
                
                if selected_mr_1 is not None:
                    for lm_1 in selected_mr_1.findall("languagemap"):
                        lm_2 = ET.SubElement(mr_2_root, "languagemap")
                        for attr, value in lm_1.attrib.items():
                            lm_2.set(attr, value)
                            
        return ET.tostring(root_2, encoding="unicode")

class SrxTransformer:
    @staticmethod
    def transform(srx_xml: str, parameter_map: Optional[Dict[str, Any]] = None) -> str:
        if 'version="1.0"' in srx_xml:
            return Srx1Transformer().transform(srx_xml, parameter_map)
        return srx_xml
