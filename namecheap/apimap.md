
NOTE: These methods work only for the domains registered with Namecheap that are currently present in your Namecheap account.

domains
getList — Returns a list of domains for the particular user.
getContacts — Gets contact information of the requested domain.
create — Registers a new domain name.
getTldList — Returns a list of tlds
setContacts — Sets contact information for the domain.
check — Checks the availability of domains.
reactivate — Reactivates an expired domain.
renew — Renews an expiring domain.
getRegistrarLock — Gets the RegistrarLock status of the requested domain.
setRegistrarLock — Sets the RegistrarLock status for a domain.
getInfo — Returns information about the requested domain.
domains.dns
setDefault — Sets domain to use our default DNS servers. Required for free services like Host record management, URL forwarding, email forwarding, dynamic dns and other value added services.
setCustom — Sets domain to use custom DNS servers. NOTE: Services like URL forwarding, Email forwarding, Dynamic DNS will not work for domains using custom nameservers.
getList — Gets a list of DNS servers associated with the requested domain.
getHosts — Retrieves DNS host record settings for the requested domain.
getEmailForwarding — Gets email forwarding settings for the requested domain
setEmailForwarding — Sets email forwarding for a domain name.
setHosts — Sets DNS host records settings for the requested domain.
domains.ns
create — Creates a new nameserver.
delete — Deletes a nameserver associated with the requested domain.
getInfo — Retrieves information about a registered nameserver.
update — Updates the IP address of a registered nameserver.
domains.transfer
create — Transfers a domain to Namecheap. You can only transfer .biz, .ca, .cc, .co, .co.uk, .com, .com.es, .com.pe, .es, .in, .info, .me, .me.uk, .mobi, .net, .net.pe, .nom.es, .org, .org.es, .org.pe, .org.uk, .pe, .tv, .us domains through API at this time.
getStatus — Gets the status of a particular transfer.
updateStatus — Updates the status of a particular transfer. Allows you to re-submit the transfer after releasing the registry lock.
getList — Gets the list of domain transfers.
ssl
create — Creates a new SSL certificate.
getList — Returns a list of SSL certificates for the particular user.
parseCSR — Parsers the CSR
getApproverEmailList — Gets approver email list for the requested certificate.
activate — Activates a newly purchased SSL certificate.
resendApproverEmail — Resends the approver email.
getInfo — Retrieves information about the requested SSL certificate
renew — Renews an SSL certificate.
reissue — Reissues an SSL certificate.
resendfulfillmentemail — Resends the fulfilment email containing the certificate.
purchasemoresans — Purchases more add-on domains for already purchased certificate.
revokecertificate — Revokes a re-issued SSL certificate.
editDCVMethod — Sets new domain control validation (DCV) method for a certificate or serves as 'retry' mechanism
users
getPricing — Returns pricing information for a requested product type.
getBalances — Gets information about fund in the user's account.This method returns the following information: Available Balance, Account Balance, Earned Amount, Withdrawable Amount and Funds Required for AutoRenew.
changePassword — Changes password of the particular user's account.
update — Updates user account information for the particular user.
createaddfundsrequest — Creates a request to add funds through a credit card
getAddFundsStatus — Gets the status of add funds request.
create — Creates a new account at NameCheap under this ApiUser.
login — Validates the username and password of user accounts you have created using the API command namecheap.users.create.
resetPassword — When you call this API, a link to reset password will be emailed to the end user's profile email id.The end user needs to click on the link to reset password.
users.address
create — Creates a new address for the user
delete — Deletes the particular address for the user.
getInfo — Gets information for the requested addressID.
getList — Gets a list of addressIDs and addressnames associated with the user account.
setDefault — Sets default address for the user.
update — Updates the particular address of the user
domainprivacy
changeemailaddress — Changes domain privacy email address
enable — Enables domain privacy protection.
disable — Disables domain privacy protection.
getList — Gets the list of domain privacy protection.
renew — Renews domain privacy protection.