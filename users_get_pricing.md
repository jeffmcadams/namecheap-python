
namecheap.users.getPricing
Returns pricing information for a requested product type.

Example Request
https://api.namecheap.com/xml.response?ApiUser=apiexample&ApiKey=56b4c87ef4fd49cb96d915c0db68194&UserName=apiexample&ClientIP=192.168.1.109&Command=namecheap.users.getPricing&ProductType=DOMAIN
Request Parameters
Global parameters are not shown here for clarity, but should be present in all requests

Name	Type	MaxLength	Required?	Description
ProductType	String	20	Yes	Product Type to get pricing information
ProductCategory	String	20	No	Specific category within a product type
PromotionCode	String	20	No	Promotional (coupon) code for the user
ActionName	String	20	No	Specific action within a product type
ProductName	String	20	No	The name of the product within a product type
Possible values for ProductType, ProductCategory, ActionName and ProductName parameters:

ProductType	Product Category	ActionName	ProductName
DOMAIN	DOMAINS	REGISTER,RENEW,REACTIVATE,TRANSFER	COM
SSLCERTIFICATE	COMODO	PURCHASE,RENEW	INSTANTSSL
Example Response
<?xml version="1.0" encoding="UTF-8"?>
<ApiResponse xmlns="http://api.namecheap.com/xml.response" Status="OK">
  <Errors />
  <RequestedCommand>namecheap.users.getPricing</RequestedCommand>
  <CommandResponse Type="namecheap.users.getPricing">
    <UserGetPricingResult>
      <ProductType Name="DOMAIN">
        <ProductCategory Name="REACTIVATE">
          <Product Name="biz">
            <Price Duration="1" DurationType="YEAR" Price="8.55" RegularPrice="8.55" YourPrice="8.55" CouponPrice="" Currency="USD" />
            <Price Duration="2" DurationType="YEAR" Price="8.87" RegularPrice="8.87" YourPrice="8.87" CouponPrice="" Currency="USD" />
          </Product>
          <Product Name="bz">
            <Price Duration="1" DurationType="YEAR" Price="8.88" RegularPrice="8.88" YourPrice="8.88" CouponPrice="" Currency="USD" />
          </Product>
        </ProductCategory>
        <ProductCategory Name="REGISTER">
          <Product Name="biz">
            <Price Duration="1" DurationType="YEAR" Price="6.00" RegularPrice="6.00" YourPrice="6.00" CouponPrice="" Currency="USD" />
            <Price Duration="2" DurationType="YEAR" Price="8.87" RegularPrice="8.87" YourPrice="8.87" CouponPrice="" Currency="USD" />
          </Product>
        </ProductCategory>
      </ProductType>
    </UserGetPricingResult>
  </CommandResponse>
  <Server>IMWS-A06</Server>
  <GMTTimeDifference>+5:30</GMTTimeDifference>
  <ExecutionTime>1.109</ExecutionTime>
</ApiResponse>
Response Parameters
Name	Description
ProductType Name	The type of product
ProductCategory Name	Category type of the product
Product Name	Name of the product
Duration	The duration of the product
DurationType	The duration type of the product
Price	Indicates Final price (it can be from regular, userprice, special price,promo price, tier price)
RegularPrice	Indicates regular price
YourPrice	The user’s price for the product
CouponPrice	Price with coupon enabled
Currency	Currency in which the price is listed
Error Codes
Specifies the error codes that might be returned from this method

Number	Description
2011170	PromotionCode is invalid
2011298	ProductType is invalid
