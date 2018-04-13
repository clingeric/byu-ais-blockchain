from django.shortcuts import render, redirect
import json, requests
import datetime, traceback
from django.contrib.auth.views import logout
from django.contrib.auth import authenticate, login
from django import template

#####
# Main View that handles all requests (Purchaser, Vendor, Facility)
# See the bottom of this view for actual, and functioning, API calls to our server
#
#####

def index(request):
    return render(request, 'account/login.html')

def login_success(request):
    """
    Redirects users based on whether they are in the admins group
    """
    user = authenticate(username=request.POST['email'], password=request.POST['password'])
    # changed from request.user to user
    if user is not None:
        login(request, user)
        print("Request Username: " + request.user.username)
        if request.user.groups.filter(name="Vendors").exists():
            print("User is a Vendor")
            return redirect("/PackageTracking/vendor/")
        elif request.user.groups.filter(name="Purchasers").exists():
            print("User is a Purchaser")
            return redirect("/PackageTracking/purchaser")
        elif request.user.groups.filter(name="Facilities").exists():
            print("User is a Facility")
            return redirect("/PackageTracking/facility")
        else:
            print("User is none of the above")
            return render(request, '/PackageTracking/index.html')
    else:
        print("User is none!")
        return redirect("/accounts/login/")

def signOut(request):
    logout(request)
    return redirect("/accounts/login/")


def purchaser(request):
    if request.user.is_authenticated:
        print("User is authenticated")
        username = request.user.username
    else:
        print("User is not authenticated")
        return redirect("/accounts/login/")
    currentPurchaser = getPurchaserID(request.user.username)
    if currentPurchaser == "No Result":
        currentPurchaser = "PURCHASER_21"
    print("Current Purchaser inside purchaser: " + currentPurchaser)
    url = "http://148.100.108.118:3000/api/org.byu.Purchaser/" + currentPurchaser
    headers = {
        'Cache-Control': "no-cache",
    }
    response = requests.request("GET", url, headers=headers)
    json_response = response.json()
    Shipments = []
    PastShipments = []
    firstName = json_response['firstName']
    lastName = json_response['lastName']
    email = json_response['email']
    incomingShipments = json_response['incomingShipments']
# Make changes to sort by date and such, or maybe in the javascript
    for shipment in json_response['incomingShipments']:
        tempShip = getShipmentInfo(shipment.split("#", 1)[1])
        if tempShip.movementStatus == "Delivered":
            PastShipments.append(tempShip)
        else:
            Shipments.append(tempShip)

    print(username)
    context = {
        'Shipments': Shipments,
        'PastShipments': PastShipments,
        'username': username,
    }
    return render(request, 'PackageTracking/purchaser.html', context)

def getPurchaserID(username):
    print("At top of getPurchaserID")
    url = "http://148.100.108.118:3000/api/org.byu.Purchaser/"
    headers = {
        'Cache-Control': "no-cache",
    }
    response = requests.request("GET", url, headers=headers)
    json_response = response.json()
    purchasers = []
    for item in json_response:
        if username == item['email']:
            return item['userID']
    return "No Result"


def vendor(request):
    if request.user.is_authenticated:
        username = request.user.username
    else:
        return redirect("/accounts/login/")

    currentVendor = getVendorID(request.user.username)
    if currentVendor == "No Result":
        currentVendor = "Amazon-Seattle@email.com"

    print(currentVendor)

    Shipments = getVendorShipments(currentVendor)

    context = {
        'Shipments': Shipments,
        'username': username,
    }
    return render(request, 'PackageTracking/vendor.html', context)

def getVendorShipments(vendorID):
    url = "http://148.100.108.118:3000/api/org.byu.Shipment/"
    headers = {
        'Cache-Control': "no-cache",
    }
    response = requests.request("GET", url, headers=headers)
    json_response = response.json()
    Shipments = []

    for item in json_response:
        tempName = "resource:org.byu.Vendor#" + vendorID
        if tempName == item['vendor']:
            print(tempName)
            print(item['vendor'])
            Shipments.append(getShipmentInfo(item['shipmentID']))
    return Shipments



def getVendorID(username):
    url = "http://148.100.108.118:3000/api/org.byu.Vendor/"
    headers = {
        'Cache-Control': "no-cache",
    }
    response = requests.request("GET", url, headers=headers)
    json_response = response.json()
    purchasers = []
    for item in json_response:
        if username == item['email']:
            return item['userID']
    return "No Result"

def facility(request):
    if request.user.is_authenticated:
        username = request.user.username
    else:
        return redirect("/accounts/login/")

    # Get Facility Information
    # username = request.POST['email']
    currentFacility = getFacilityID(request.user.username)
    if currentFacility == "No Result":
        currentFacility = "UPS-Seattle@email.com"
    url = "http://148.100.108.118:3000/api/org.byu.FACILITY/" + currentFacility
    headers = {
        'Cache-Control': "no-cache",
    }
    response = requests.request("GET", url, headers=headers)
    json_response = response.json()
    # print(json_response)
    # print(json_response['userID'])
    id = json_response['userID']
    facilityName = json_response['facilityName']
    Address1 = json_response['Address1']
    Address2 = json_response['Address2']
    City = json_response['City']
    State = json_response['State']
    Country = json_response['Country']
    ZipCode = json_response['ZipCode']
    incomingShipments = json_response['incomingShipments']
    currentShipments = json_response['currentShipments']

    incomingShipments = []
    inFacility = []
    inTransit = []
    OutForShipments = []
    DeliveredShipments = []
    OtherShipments = []

    for shipment in json_response['incomingShipments']:
        tempShip = getShipmentInfo(shipment.get("shipmentID"))
        incomingShipments.append(tempShip)
    # print(incomingShipments)

    for shipment in json_response['currentShipments']:
        tempShip = getShipmentInfo(shipment.get("shipmentID"))
        if tempShip.movementStatus == "In Facility":
            inFacility.append(tempShip)
        elif tempShip.movementStatus == "In Transit":
            inTransit.append(tempShip)
        elif tempShip.movementStatus == "Out For Delivery":
            OutForShipments.append(tempShip)
        elif tempShip.movementStatus == "Delivered":
            DeliveredShipments.append(tempShip)
        else:
            OtherShipments.append(tempShip)

    context = {
        'incomingShipments': incomingShipments,
        'inFacility': inFacility,
        'inTransit': inTransit,
        'OutForShipments': OutForShipments,
        'DeliveredShipments': DeliveredShipments,
        'OtherShipments': OtherShipments,
        'username': username,
    }
    return render(request, 'PackageTracking/facility.html', context)

def getFacilityID(username):
    url = "http://148.100.108.118:3000/api/org.byu.Facility/"
    headers = {
        'Cache-Control': "no-cache",
    }
    response = requests.request("GET", url, headers=headers)
    json_response = response.json()
    purchasers = []
    for item in json_response:
        if username == item['email']:
            return item['userID']
    return "No Result"


# Example function that does nothing rn
def send_package(request, shipmentID):
    print('this is a request to send_package %s' % shipmentID)
    return redirect('facility')

def SendShipment(request):
    if request.method == "POST":
        # print(request.POST['toFacility'])
        toFacility = getFacilityID(request.POST['toFacility'] + "@email.com")
        # print(toFacility)
        shipmentID = request.POST['shipmentID']
        # print(shipmentID)
    data = {
        "toFacility": toFacility,
        "shipment": shipmentID
    }
    data_json = json.dumps(data)
    url = "http://148.100.108.118:3000/api/org.byu.SendShipment/"
    headers = {
        'Content-Type': "application/json",
    }
    response = requests.post(url, data=data_json, headers=headers)
    # print(response.text)
    return redirect('facility')

def ReceiveShipment(request, shipmentID):
    # print("At top of ReceiveShipment")
    currentFacility = getFacilityID(request.user.username)
    tempship = getShipmentInfo(shipmentID)
    # print(tempship.currentFacility)
    previousFacility = getPrevFacility(shipmentID)
    data = {
        "currentFacility": currentFacility,
        "previousFacility": previousFacility,
        "shipment": shipmentID
    }
    data_json = json.dumps(data)
    url = "http://148.100.108.118:3000/api/org.byu.ReceiveShipment/"
    headers = {
        'Content-Type': "application/json",
    }
    response = requests.post(url, data=data_json, headers=headers)
    return redirect('facility')

def getPrevFacility(shipmentID):
    url = "http://148.100.108.118:3000/api/org.byu.Shipment/" + shipmentID
    headers = {
        'Cache-Control': "no-cache",
    }
    response = requests.request("GET", url, headers=headers)
    json_response = response.json()
    return json_response['currentFacility']




def OutForDelivery(request, shipmentID):
    data = {
        "shipment": shipmentID,
    }
    data_json = json.dumps(data)
    url = "http://148.100.108.118:3000/api/org.byu.OutForDelivery/"
    headers = {
        'Content-Type': "application/json",
    }
    response = requests.post(url, data=data_json, headers=headers)
    return redirect('facility')

def DeliverShipment(request, shipmentID):
    notes = "Left on doorstep"
    data = {
        "dropOffNotes": notes,
        "shipment": shipmentID
    }
    data_json = json.dumps(data)
    url = "http://148.100.108.118:3000/api/org.byu.DeliverShipment/"
    headers = {
        'Content-Type': "application/json",
    }
    response = requests.post(url, data=data_json, headers=headers)
    return redirect('facility')

def InitialReceive(currentFacility, purchaser, shipment):
    data = {
        "currentFacility": currentFacility,
        "purchaser": purchaser,
        "shipment": shipment
    }
    data_json = json.dumps(data)
    url = "http://148.100.108.118:3000/api/org.byu.InitialReceive/"
    headers = {
        'Content-Type': "application/json",
    }
    response = requests.post(url, data=data_json, headers=headers)
    # print("Response: " + response.text)

def getShipmentInfo(shipment):
    # print("At top of getShipmentInfo")
    # print(shipment)
    url = "http://148.100.108.118:3000/api/org.byu.Shipment/" + shipment
    headers = {
        'Cache-Control': "no-cache",
    }
    response = requests.request("GET", url, headers=headers)
    json_response = response.json()


    if 'currentFacility' not in json_response:
        tempShip = Shipment(json_response['shipmentID'],
                            getVendorName(json_response['vendor']),
                            json_response['purchaser'],
                            'No Facility',
                            json_response['destAddress'],
                            json_response['estDeliveryDate'],
                            json_response['deliveryService'],
                            getStatusInfo(json_response['movementStatus']),
                            'Signature',
                            json_response['containedItems'],
                            json_response['weight'],)
        return(tempShip)
    else:
        currFacility = getFacilityName(json_response['currentFacility'])
        tempShip = Shipment(json_response['shipmentID'],
                            getVendorName(json_response['vendor']),
                            json_response['purchaser'],
                            currFacility,
                            json_response['destAddress'],
                            json_response['estDeliveryDate'],
                            json_response['deliveryService'],
                            getStatusInfo(json_response['movementStatus']),
                            'Signature',
                            json_response['containedItems'],
                            json_response['weight'], )
        return (tempShip)

def getStatusInfo(movementStatus):
    statuses = {
        'IN_FACILITY': 'In Facility',
        'OUT_FOR_DELIVERY': 'Out For Delivery',
        'IN_TRANSIT': 'In Transit',
        'DELIVERED': 'Delivered',
        'IN_VENDOR_POSSESSION': 'In Vendor Possession'
    }
    status = statuses[movementStatus]
    return status

def getVendorName(vendorID):
    vendors = {
        'resource:org.byu.Vendor#VENDOR_1': 'Walmart',
        'resource:org.byu.Vendor#VENDOR_2': 'Target',
        'resource:org.byu.Vendor#VENDOR_3': 'Amazon',
        'resource:org.byu.Vendor#VENDOR_4': "Dick's",
    }
    vendor = vendors[vendorID]
    return vendor

def getFacilityName(facilityID):
    # print(facilityID)
    facilities = {
        'resource:org.byu.Facility#FACILITY_21': 'UPS Burlington, MA',
        'resource:org.byu.Facility#FACILITY_22': 'UPS Seattle, WA',
        'resource:org.byu.Facility#FACILITY_23': 'UPS Salt Lake City, UT',
        'resource:org.byu.Facility#FACILITY_24': 'DHL Yuba City, CA',
        'resource:org.byu.Facility#FACILITY_25': 'J.B. Hunt Matthews, NC',
        'resource:org.byu.Facility#FACILITY_26': 'Fedex Gynn Oak, MD',
        'resource:org.byu.Facility#FACILITY_27': 'USPS Bel Air, MD',
        'resource:org.byu.Facility#FACILITY_28': 'UPS Ronkonkoma, NY',
        'resource:org.byu.Facility#FACILITY_29': 'DHL Antioch, TN',
        'resource:org.byu.Facility#FACILITY_210': 'J.B. Hunt Saint Paul, MN',
        'resource:org.byu.Facility#FACILITY_211': 'Fedex Onalaska, WI',
        'resource:org.byu.Facility#FACILITY_212': 'USPS Wake Forest, NC',
        'resource:org.byu.Facility#FACILITY_213': 'UPS Buffalo, NY',
        'resource:org.byu.Facility#FACILITY_214': 'DHL Woburn, MA',
    }
    facilityName = facilities[facilityID]
    # facility = facilityID.split("#", 1)[1]
    # print(facility)
    # url = "http://148.100.108.118:3000/api/org.byu.Facility/" + facility
    # headers = {
    #     'Cache-Control': "no-cache",
    # }
    # response = requests.request("GET", url, headers=headers)
    # json_response = response.json()
    # facilityName = json_response['facilityName'] + " " + json_response['City'] + ", " + json_response['State']
    return facilityName


class Shipment:
    def __init__(self, shipmentID, vendor, purchaser, currentFacility, destAddress, estDeliveryDate,
                 deliveryService, movementStatus, signature, containedItems, weight):
        self.shipmentID = shipmentID
        self.vendor = vendor
        self.purchaser = purchaser
        self.currentFacility = currentFacility
        self.destAddress = destAddress
        self.estDeliveryDate = estDeliveryDate
        self.deliveryService = deliveryService
        self.movementStatus = movementStatus
        self.signature = signature
        self.containedItems = containedItems
        self.weight = weight

class Item:
    def __init__(self, itemID, itemName, serialNo, quantityOfItem):
        self.itemID = itemID
        self.itemName = itemName
        self.serialNo = serialNo
        self.quantityOfItem = quantityOfItem






##################################################################################################

def apiCalls(request):
    # Get all packages
    url = "http://148.100.108.118:3000/api/org.byu.Shipment"
    headers = {
        'Cache-Control': "no-cache",
    }
    response = requests.request("GET", url, headers=headers)
    json_response = response.json()

    # Get all Items
    Items = []
    url = "http://148.100.108.118:3000/api/org.byu.Item"
    headers = {
        'Cache-Control': "no-cache",
    }
    response = requests.request("GET", url, headers=headers)
    json_items = response.json()
    j = 0
    for item in json_items:
        id = json_items[j]['itemID']
        name = json_items[j]['itemName']
        serial = json_items[j]['serialNo']
        quantity = json_items[j]['quantityOfItem']
        tempItem = Item(id, name, serial, quantity)
        Items.append(tempItem)
        j = j + 1

# def facility(request):
#     print('At top of facility')
#     incomingPackages = []
#     inFacility = []
#     outgoing = []
#     for i in range(1, 4):
#         id = i
#         vendor = "Amazon"
#         purch = "Purchaser"
#         currFac = "Fedex Provo"
#         destAddr = "5493 West River Street Provo UT 84606"
#         estdate = "3/12/2018"
#         service = "Fedex"
#         status = "In Transit"
#         sign = "N/A"
#         items = ["Basketball", "Soccer Ball", "Baseball Glove", "Hockey Stick"]
#         tempPackage1 = Package("Incoming" + str(id), vendor, purch, currFac, destAddr, estdate, service, status, sign, items)
#         tempPackage2 = Package("Facility" + str(id), vendor, purch, currFac, destAddr, estdate, service, status, sign, items)
#         tempPackage3 = Package("Outgoing" + str(id), vendor, purch, currFac, destAddr, estdate, service, status, sign, items)
#         incomingPackages.append(tempPackage1)
#         inFacility.append(tempPackage2)
#         outgoing.append(tempPackage3)
#         print(len(incomingPackages))
#     context = {
#         'incomingPackages': incomingPackages,
#         'inFacility': inFacility,
#         'outgoing': outgoing,
#     }
#     return render(request, 'PackageTracking/facility.html', context)

    currentPurchaser = "PURCHASER_1"
#
#
#     Packages = []
#     i = 0
#     for shipment in json_response:
#         id = json_response[i]['shipmentID']
#         vendor = json_response[i]['vendor']
#         purch = json_response[i]['purchaser']
#         currFac = json_response[i]['currentFacility']
#         destAddr = json_response[i]['destAddress']
#         estdate = json_response[i]['estDeliveryDate']
#         service = json_response[i]['deliveryService']
#         status = json_response[i]['movementStatus']
#         sign = "N/A"
#         items = json_response[i]['containedItems']
#         tempPackage = Package(id, vendor, purch, currFac, destAddr, estdate, service, status, sign, items)
#         Packages.append(tempPackage)
#         i = i + 1
#
#
#     context = {
#         'Packages': Packages,
#     }
#     return render(request, 'PackageTracking/purchaser.html', context)



# def purchaser(request):
#     Packages = []
#     for i in range(1, 4):
#         id = "Shipment" + str(i)
#         vendor = "Amazon"
#         purch = "Purchaser"
#         currFac = "Fedex Provo"
#         destAddr = "5493 West River Street Provo UT 84606"
#         estdate = "3/12/2018"
#         service = "Fedex"
#         status = "In Transit"
#         sign = "N/A"
#         items = ["Basketball", "Soccer Ball", "Baseball Glove", "Hockey Stick"]
#         tempPackage = Package(id, vendor, purch, currFac, destAddr, estdate, service, status, sign, items)
#         Packages.append(tempPackage)
#     context = {
#         'Packages': Packages,
#     }
#     return render(request, 'PackageTracking/purchaser.html', context)

#def vendor(request):
#     if request.user.is_authenticated:
#         username = request.user.username
#     else:
#         return redirect("/accounts/login/")
#     Shipments = []
#     for i in range(1, 4):
#         id = "Shipment" + str(i)
#         vendor = "Amazon"
#         purch = "Purchaser"
#         currFac = "Fedex Provo"
#         destAddr = "5493 West River Street Provo UT 84606"
#         estdate = "3/12/2018"
#         service = "Fedex"
#         status = "In Transit"
#         sign = "N/A"
#         items = ["Basketball", "Soccer Ball", "Baseball Glove", "Hockey Stick"]
#         tempShipment = Shipment(id, vendor, purch, currFac, destAddr, estdate, service, status, sign, items, weight)
#         Shipments.append(tempShipment)
#     context = {
#         'Packages': Shipments,
#         'username': username,
#     }
#     return render(request, 'PackageTracking/vendor.html', context)