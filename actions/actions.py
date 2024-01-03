# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.events import AllSlotsReset

import requests
import locale
import difflib
import json
from datetime import datetime

API_ENDPOINT = "http://127.0.0.1:8000/api"

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

def matchOrderStatusToText(value: str) -> str:
    """
    Match order status to Vietnamese text
    ::param value: str
    ::return: str
    """ 
    match_dict = {
        "created": "Khởi tạo",
        "waiting_payment": "Chờ thanh toán", 
        "waiting_confirm_payment": "Chờ xác nhận thanh toán", 
        "waiting_confirm": "Chờ xác nhận", 
        "packing": "Đang chuẩn bị", 
        "waiting_shipment": "Chờ giao hàng", 
        "shipping": "Đang giao", 
        "delivered": "Đã giao", 
        "completed": "Hoàn thành", 
        "cancel_waiting_refund": "Hủy & Chờ hoàn trả", 
        "canceled_refund": "Hủy & Hoàn trả", 
        "canceled": "Đã hủy", 
        "return_waiting_refund": "Trả hàng & Chờ hoàn trả", 
        "returned": "Đã trả hàng", 
    }
    return match_dict[value]

def matchBooleanToText(value: bool) -> str:
    """
    Match boolean to Vietnamese text
    ::param value: boolean
    ::return: "có" | "không"
    """
    if value:
        return "Có"
    else:
        return "Không"
    
def matchOrdinalStringToNumber(value: str) -> float:
    """
    Match ordinal string to number
    ::param value: string
    ::return: float
    """
    valueCaseInsensitive = value.lower()
    if valueCaseInsensitive in ["trên","đầu","một", "1", "nhất"]:
        return 0
    elif valueCaseInsensitive in ["hai" , "2" , "nhị"]:
        return 1
    elif valueCaseInsensitive in ["ba" , "3" , "tam"]:
        return 2
    elif valueCaseInsensitive in ["bốn" , "4" , "tứ"]:
        return 3
    elif valueCaseInsensitive in ["dưới","cuối","năm" , "5" , "ngũ"]:
        return 4
    else:
        return -1
    
def changeCurrencyFormat(value):
    """
    Convert value to VND currency format

    ::param value: float | string

    :return: VND currency format
    """
    locale.setlocale(locale.LC_ALL, 'vi_vn')
    return locale.currency(float(value), grouping=True)

def changeTimeFormat(value: str):
    """
    Convert value to time  format

    ::param value: string

    :return: time format
    """
    print(value)
    return datetime.fromisoformat(value.replace("Z","+00:00")).strftime("%Y-%m-%d %H:%M:%S")
    

def getClosestMatches(value, valueList):
    """
    Get the closest match to the value

    ::param value: string
    ::param valueList: list

    :return: the value of the closest match
    """
    listOfClosestMatch = difflib.get_close_matches(value,valueList,1,0.6)
    if len(listOfClosestMatch) == 0:
        return None
    else:
        return listOfClosestMatch[0]
    

def resolveProductMention(tracker:Tracker) -> dict:
    """
    Get the id of the entity the user referred to by ordinal number

    :param tracker: Tracker
    :param entity_type: the entity type

    :return: the id of the actual entity (value of key attribute in the knowledge base)
    """
    mention = tracker.get_slot("mention")
    listed_products = tracker.get_slot("listed_products")

    if mention is not None and listed_products is not None:
        idx = matchOrdinalStringToNumber(mention)

        if type(idx) is int and idx < len(listed_products):
            return listed_products[idx]['id']
        
    # Return none if we can't find the mention product entity
    return None

def resolveOrderMention(tracker:Tracker) -> dict:
    """
    Get the id of the entity the user referred to by ordinal number

    :param tracker: Tracker
    :param entity_type: the entity type

    :return: the id of the actual entity (value of key attribute in the knowledge base)
    """
    mention = tracker.get_slot("mention")
    listed_orders = tracker.get_slot("listed_orders")

    if mention is not None and listed_orders is not None:
        idx = matchOrdinalStringToNumber(mention)

        if type(idx) is int and idx < len(listed_orders):
            return listed_orders[idx]['id']
        
    # Return none if we can't find the mention order entity
    return None

def resolve_entity_name(tracker: Tracker):
    """
    Get the id of the entity the user referred to. Either the NER detected the
    entity and stored its name in the corresponding slot or the user referred to
    the entity by an ordinal number, such as first or last, or the user refers to
    an entity by its attributes.

    :param tracker: Tracker
    :param entity_type: the entity type

    :return: the id of the actual entity (value of key attribute in the knowledge base)
    """

    # user referred to an entity by an ordinal number
    mention = tracker.get_slot("mention")

    if mention is not None:
        return resolveProductMention(tracker)

    # # user named the entity
    # entity_name = tracker.get_slot(entity_type)
    # if entity_name:
    #     return entity_name

    # user referred to an entity by its attributes
    # listed_items = tracker.get_slot("listed_items")
    # attributes = get_attributes_of_entity(entity_type, tracker)

    # if listed_items and attributes:
    #     # filter the listed_items by the set attributes
    #     graph_database = GraphDatabase()
    #     for entity in listed_items:
    #         key_attr = schema[entity_type]["key"]
    #         result = graph_database.validate_entity(
    #             entity_type, entity, key_attr, attributes
    #         )
    #         if result is not None:
    #             return to_str(result, key_attr)

    return None


class resetAllSlot(Action):
    def name(self) -> Text:
        return "action_reset_all_slot"
    def run(self,dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any]) -> List[Dict[Text,Any]]:
        return [AllSlotsReset()]

class searchOrder(Action):
    def name(self) -> Text:
        return "action_search_order"
    def run(self,dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any]) -> List[Dict[Text,Any]]:
        metadata = tracker.latest_message.get("metadata")
        if not metadata['user'] or not metadata['token']:
            dispatcher.utter_message("Xin lỗi, bạn cần phải đăng nhập tài khoản để kiểm tra thông tin về đơn hàng.")
            return []

        if 'id' not in metadata['user'] or not metadata['user']['id']:
            dispatcher.utter_message("Xin lỗi, thông tin đăng nhập của bạn không hợp lệ. Bạn vui lòng đăng nhập lại để kiểm tra thông tin về đơn hàng.")
            return []
        
        payload = {
            "customerId": metadata['user']['id'],
            "type": "all",
            "offset": 0,
            "limit": 5
        }

        response = requests.post(API_ENDPOINT + "/getOrders", auth=BearerAuth(metadata['token']), data=payload)
        
        if (response.status_code) == 422:
                dispatcher.utter_message("Xin lỗi, thông tin về tài khoản của bạn không tồn tại trong hệ thống. Bạn vui lòng đăng nhập để tìm kiếm thông tin đơn hàng.")
                return []
        if (response.status_code) == 401:
                dispatcher.utter_message("Xin lỗi, thông tin đăng nhập của bạn không hợp lệ. Bạn vui lòng đăng nhập lại để tìm kiếm thông tin đơn hàng.")
                return []
        # If request is not success
        if (response.status_code) != 200:
            dispatcher.utter_message("Xin lỗi, có lỗi xảy ra khi tôi đang kiểm tra thông tin đơn hàng của bạn. Bạn vui lòng thử lại sau. :<")
            return []
        
        # If request is success
        orders = response.json()['result']['orders']
        if (orders and len(orders) == 0):
            dispatcher.utter_message("Hiện tại bạn chưa có đơn hàng nào.")
            return []
        message_response = "Dưới đây là thông tin về 5 đơn hàng gần đây nhất của bạn: "
        orderIds = []
        count = 1
        for order in orders:
            message_response = message_response + f"""
{str(count)}. Mã đơn: #{order['order_code']}
- Tổng giá trị đơn hàng: {changeCurrencyFormat(order['subtotal'])}.
- Tình trạng hiện tại: {matchOrderStatusToText(order['status'])}.
- Được tạo vào lúc: {changeTimeFormat(order['created_at'])}
            """
            count = count + 1
            orderIds.append(order['id'])
        
        response = {"message": message_response, "orders": orderIds}
        dispatcher.utter_message(json.dumps(response,ensure_ascii=False))
        return [SlotSet("listed_orders", orders)]


class searchProduct(Action):
    def name(self) -> Text:
        return "action_search_product"
    def run(self,dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any]) -> List[Dict[Text,Any]]:
       
        product_keyword = tracker.get_slot("product_keyword")
       
        payload = {
            "sort": "common",
            "offset": 0,
            "limit": 5,
            "keyword": product_keyword
        }
       
        response = requests.get(API_ENDPOINT + "/productByFilter",params = payload)
        # If request is not success
        if (response.status_code) != 200:
            dispatcher.utter_message("Xin lỗi, có lỗi xảy ra khi tôi đang tìm kiếm sản phẩm này. Bạn vui lòng thử lại sau. :<")
            return [SlotSet("product_keyword", None)]
        
        # If request is success
        products = response.json()['result']['product']
        # If there is no match product
        if len(products) == 0:
            dispatcher.utter_message("Xin lỗi, nhưng tôi không thể tìm thấy sản phẩm phù hợp với yêu cầu của bạn. Bạn có thể cung cấp thêm thông tin về sản phẩm bạn đang tìm kiếm để tôi có thể hỗ trợ bạn tốt hơn không?")
            return [SlotSet("product_keyword", None)]


        message_response = "Tôi có một số lựa chọn \"" +  product_keyword + "\" cho bạn:\n"
        count = 1
        productIds = []
        for product in products:
            if (product["max_discount_amount"]):
                message_response = message_response + str(count) + ". " + product['name'] + " - Giá gốc: " + changeCurrencyFormat(product["price"]) + ". Hiện đang giảm giá còn: " + changeCurrencyFormat(product["priceDiscount"]) + "\n"  
            else: 
                message_response = message_response + str(count) + ". " + product['name'] + " - Giá: " + changeCurrencyFormat(product["price"]) + "\n" 
            productIds.append(product['id'])
            count += 1
        response = {"message": message_response, "products": productIds, "product_keyword": product_keyword}
        dispatcher.utter_message(json.dumps(response,ensure_ascii=False))
      
        # Clear product_keywrod slot, Add items to list_product slots
        return [SlotSet("product_keyword", None),  SlotSet("listed_products", products)]

class action_resolve_product_entity(Action):
    def name(self) -> Text:
        return "action_resolve_product_entity"
    def run(self,dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any]) -> List[Dict[Text,Any]]:
        # Get the product entity user wants to see
        # Check if entity was mentioned as 'first', 'second', etc.
        mention = tracker.get_slot("mention")
        if mention is not None:
            value = resolveProductMention(tracker)
            if value is not None:
                return [SlotSet("product_entity_id", value), SlotSet("mention", None)]
        
        # #  Check if NER recognized entity directly
        # # (e.g. name was mentioned and recognized as 'bánh tráng',...)

        # # Get value and closest possible match from entity directly
        # value = tracker.get_slot("product_entity")
        # closestMatches = getClosestMatches(value,listed_products)

        # if (value is not None) and (closestMatches is not None):
        #     # Get the id of the correspond match

        #     return [SlotSet("product_entity", closestMatches), SlotSet("mention", None)]

        # If we can not resolve user product_entity
        return [SlotSet("product_entity_id", None), SlotSet("mention", None)]

class action_resolve_order_entity(Action):
    def name(self) -> Text:
        return "action_resolve_order_entity"
    def run(self,dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any]) -> List[Dict[Text,Any]]:
        # Get the order entity user wants to see
        # Check if entity was mentioned as 'first', 'second', etc.
        mention = tracker.get_slot("mention")
        if mention is not None:
            value = resolveOrderMention(tracker)
            if value is not None:
                return [SlotSet("order_entity_id", value), SlotSet("mention", None)]
        
        # #  Check if NER recognized entity directly
        # # (e.g. name was mentioned and recognized as 'bánh tráng',...)

        # # Get value and closest possible match from entity directly
        # value = tracker.get_slot("product_entity")
        # closestMatches = getClosestMatches(value,listed_products)

        # if (value is not None) and (closestMatches is not None):
        #     # Get the id of the correspond match

        #     return [SlotSet("product_entity", closestMatches), SlotSet("mention", None)]

        # If we can not resolve user order_entity
        return [SlotSet("order_entity_id", None), SlotSet("mention", None)]
    

class action_get_product(Action):
  
    def name(self) -> Text:
        return "action_get_product"
    def run(self,dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any]) -> List[Dict[Text,Any]]:
        product_entity_id = tracker.get_slot("product_entity_id")
        if product_entity_id is None:
            dispatcher.utter_message("Xin lỗi, tôi không thể tìm được sản phẩm cụ thể mà bạn muốn nhắc đến. Bạn có thể cung cấp thêm thông tin hoặc đặt câu hỏi cụ thể hơn được không? Tôi sẽ cố gắng giúp bạn.")
        else: 
            payload = {
                "id" : product_entity_id
            }
            # Get product detail
            response = requests.get(API_ENDPOINT + "/productDetail", params=payload)
            if (response.status_code) != 200:
                dispatcher.utter_message("Xin lỗi, có lỗi xảy ra khi tôi đang tìm kiếm sản phẩm này. Bạn vui lòng thử lại sau. :<")
                return [SlotSet("product_entity_id", None)]
            
            # If request is success
            product = response.json()['result']['product']
            # If there is no match product
            if product is None:
                dispatcher.utter_message("Xin lỗi, nhưng tôi không thể tìm thấy sản phẩm phù hợp với yêu cầu của bạn. Bạn có thể cung cấp thêm thông tin về sản phẩm bạn đang tìm kiếm để tôi có thể hỗ trợ bạn tốt hơn không?")

            message_response = \
            f"""Dưới đây là thông tin về sản phẩm \"{product['name']}\" trong danh sách sản phẩm:
Thông tin sản phẩm:
    - Xuất xứ: {product['origin']}
    - Hạn sử dụng: {product['exp_date']}
    - Hướng dẫn bảo quản: {'Không' if product['directionForPreservation'] == "None" else product['directionForPreservation']}
    - Hướng dẫn sử dụng: {'Không' if product['directionForUse'] == "None" else product['directionForUse']}
    - Trọng lượng sản phẩm: {product['weight']}
    - Quy cách đóng gói: {product['pack']}
    - Thành phần: {product['ingredient']}
Đánh giá chung:
    - Phân loại sản phẩm sỉ: {matchBooleanToText(product['is_wholesale'])} 
    - Số lượng hàng tồn kho còn lại: {product['quantity_available']}
    - Số lượt đánh giá: {product['nums_of_reviews']} 
    - Số lượt thích: {product['nums_of_like']} 
    - Đánh giá: {product['rating']} Sao 
Giá: 
    - Giá gốc: {changeCurrencyFormat(product['price'])} 
    {'- Giá khuyến mãi: ' + changeCurrencyFormat(product['priceDiscount']) if product["max_discount_amount"] else ''}       
Nếu bạn có bất kỳ câu hỏi nào khác hoặc cần thêm thông tin, hãy để tôi biết!
                """
            dispatcher.utter_message(message_response)
            
        return [SlotSet("product_entity_id", None)]
    
class action_get_order(Action):
  
    def name(self) -> Text:
        return "action_get_order"
    def run(self,dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any]) -> List[Dict[Text,Any]]:
        metadata = tracker.latest_message.get("metadata")
        if not metadata['user'] or not metadata['token']:
            dispatcher.utter_message("Xin lỗi, bạn cần phải đăng nhập tài khoản để kiểm tra thông tin về đơn hàng.")
            return [SlotSet("product_keyword", None)]

        if 'id' not in metadata['user'] or not metadata['user']['id']:
            dispatcher.utter_message("Xin lỗi, thông tin đăng nhập của bạn không hợp lệ. Bạn vui lòng đăng nhập lại để kiểm tra thông tin về đơn hàng.")
            return [SlotSet("product_keyword", None)]
        
        order_entity_id = tracker.get_slot("order_entity_id")
        if order_entity_id is None:
            dispatcher.utter_message("Xin lỗi, tôi không thể tìm được đơn hàng cụ thể mà bạn muốn nhắc đến. Bạn có thể cung cấp thêm thông tin hoặc đặt câu hỏi cụ thể hơn được không? Tôi sẽ cố gắng giúp bạn.")
        else: 
            payload = {
            "orderId" : order_entity_id,
            "customerId": metadata['user']['id']
         
            }
            # Get order detail
            response = requests.post(API_ENDPOINT + "/getOrderDetail", auth=BearerAuth(metadata['token']),params=payload)
            if (response.status_code) == 422:
                dispatcher.utter_message("Xin lỗi, thông tin về tài khoản của bạn không tồn tại trong hệ thống. Bạn vui lòng đăng nhập để tìm kiếm thông tin đơn hàng.")
                return [SlotSet("order_entity_id", None)]
            if (response.status_code) == 401:
                dispatcher.utter_message("Xin lỗi, thông tin đăng nhập của bạn không hợp lệ. Bạn vui lòng đăng nhập lại để tìm kiếm thông tin đơn hàng.")
                return [SlotSet("order_entity_id", None)]
            if (response.status_code) != 200:
                dispatcher.utter_message("Xin lỗi, có lỗi xảy ra khi tôi đang tìm kiếm thông tin về đơn hàng này. Bạn vui lòng thử lại sau. :<")
                return [SlotSet("order_entity_id", None)]
            
            # If request is success
            order = response.json()['result']['order']
            # If there is no match product
            if order is None:
                dispatcher.utter_message("Xin lỗi, nhưng tôi không thể tìm thấy đơn hàng của bạn. Bạn có thể cung cấp thêm thông tin về đơn hàng bạn đang tìm kiếm để tôi có thể hỗ trợ bạn tốt hơn không?")

            message_response = f"""Sau đây là thông tin chi tiết của đơn hàng {order['order_code']}:
1. Tình trạng đơn hàng: {matchOrderStatusToText(order['status'])}
2. Thông tin thanh toán đơn hàng:
    - Phương thức thanh toán: {order['payment_method']}
    - Tổng thanh toán: {changeCurrencyFormat(order['subtotal'])}
    - Phí vận chuyển: {changeCurrencyFormat(order['shipping_subtotal'])}
    - Giảm giá đơn hàng: {changeCurrencyFormat(order['voucher_discount'])}
3. Chi tiết đơn hàng:"""
            for order_detail in order['order_detail']:
                message_response = message_response + f"""
- Sản phẩm: {order_detail['product']['name']}, đơn giá: {order_detail['unit_discount']}, số lượng: {order_detail['quantity']} sản phẩm."""
            
            orderId = order['id']
            message_response = message_response + "\nNếu bạn có bất kỳ câu hỏi nào khác hoặc cần thêm thông tin, hãy để tôi biết!"
            response = {"message": message_response, "order": orderId}
            dispatcher.utter_message(json.dumps(response,ensure_ascii=False))
        
        return []
    
