import random
import re
from json import JSONDecodeError
from urllib.parse import urlencode

from locust import HttpUser, task, run_single_user
#from locust_plugins.csvreader import CSVReader

LEGACY_LOGIN = True
SITE_USER = "Admin"
SITE_PASSWD = "admin123"
INSUREE_IDS = ["070707070"]
API_ROOT = "/iapi" if LEGACY_LOGIN else "/api"  # api or ipai, feel free to override if necessary
HF_UUID = "E4C10505-AFC5-4E44-9E70-C9993B3CEE4B"  # Release
# HF_UUID = "05EF3CA3-6B37-4793-8714-6CFE97B7B639"  # Eric
HF_PARENT_UUID = "1DBB7008-9CF8-4D1E-9AAD-1487DD0E813E"  # Release
# HF_PARENT_UUID = "353218AE-0F97-4580-B529-9DF7BEA49BE6"  # Eric


#insuree_reader = CSVReader("insuree_numbers.csv")

class SimpleUser(HttpUser):
    @task
    def current_user(self):
        self.client.get(f"{API_ROOT}/core/users/current_user/")

    @task
    def list_claims(self):
        self.client.post(
            f"{API_ROOT}/graphql",
            json={
                "query": """
                {
                      claims(status: 2, healthFacility_Location_Parent_Uuid: "%s", 
                      healthFacility_Location_Uuid: "%s",orderBy: ["-dateClaimed"],
                      first: 10)
                    {
                        totalCount
                        pageInfo { hasNextPage, hasPreviousPage, startCursor, endCursor}
                        edges {      
                            node {
                                uuid,code,jsonExt,dateClaimed,feedbackStatus,reviewStatus,claimed,approved,status,
                                healthFacility { id uuid name code },insuree{id, uuid, chfId, lastName, otherNames},
                                attachmentsCount
                            }
                        }
                    }
                }""" % (HF_PARENT_UUID, HF_UUID)
            },
            name="list_claims"
        )

    @task
    def eligibility(self):
        insuree_id = random.choice(INSUREE_IDS)
        #(insuree_id,) = next(insuree_reader)
        self.client.post(
            f"{API_ROOT}/graphql",
            json={
                "query": """
                {
                  insurees(chfId: "%s") {
                    pageInfo {
                      hasNextPage
                      hasPreviousPage
                      startCursor
                      endCursor
                    }
                    edges {
                      node {
                        id
                        uuid
                        chfId
                        lastName
                        otherNames
                        dob
                        age
                        validityFrom
                        validityTo
                        gender { code }
                        family { id }
                        photo { folder filename photo }
                        gender { code gender altLanguage }
                        healthFacility {
                          id
                          uuid
                          code
                          name
                          level
                          servicesPricelist { id uuid }
                          itemsPricelist { id uuid }
                          location {
                            id uuid code name
                            parent { id uuid code name }
                          }
                        }
                      }
                    }
                  }
                }""" % (insuree_id,)
            },
            name="insurees"
        )
        self.client.post(
            f"{API_ROOT}/graphql",
            json={
                "query": """
                {
                  policiesByInsuree(orderBy: "expiryDate", activeOrLastExpiredOnly: true, chfId: "%s", first: 5) {
                    totalCount
                    pageInfo {
                      hasNextPage
                      hasPreviousPage
                      startCursor
                      endCursor
                    }
                    edges {
                      node {
                        policyUuid
                        productCode
                        productName
                        officerCode
                        officerName
                        enrollDate
                        effectiveDate
                        startDate
                        expiryDate
                        status
                        policyValue
                        balance
                        ded
                        dedInPatient
                        dedOutPatient
                        ceiling
                        ceilingInPatient
                        ceilingOutPatient
                      }
                    }
                  }
                }""" % (insuree_id,)
            },
            name="policiesByInsuree"
        )
        with self.client.post(
                f"{API_ROOT}/graphql",
                json={
                    "query": """
                {
                  policiesByInsuree(orderBy: "expiryDate", activeOrLastExpiredOnly: true, chfId: "%s", first: 5) {
                    totalCount
                    pageInfo {
                      hasNextPage
                      hasPreviousPage
                      startCursor
                      endCursor
                    }
                    edges {
                      node {
                        policyUuid
                        productCode
                        productName
                        officerCode
                        officerName
                        enrollDate
                        effectiveDate
                        startDate
                        expiryDate
                        status
                        policyValue
                        balance
                        ded
                        dedInPatient
                        dedOutPatient
                        ceiling
                        ceilingInPatient
                        ceilingOutPatient
                      }
                    }
                  }
                }""" % (insuree_id,)
                },
                catch_response=True,
                name="policiesByInsuree2"
        ) as response:
            try:
                print("Got response", response.text)
                j = response.json()
                policyUuid = j["data"]["policiesByInsuree"]["edges"][0]["node"]["policyUuid"]
                print("Uuid: ", policyUuid)
            except KeyError:
                print("Key Error", response.text)
                response.failure("Couldn't find a policy in the response")
            except JSONDecodeError:
                print("JSON Error", response.text)
                response.failure("Couldn't decode policy response JSON")

        self.client.post(
            f"{API_ROOT}/graphql",
            json={
                "query": """
                {
                  premiumsByPolicies(orderBy: "-payDate", policyUuids: ["%s"], first: 5) {
                    totalCount
                    pageInfo {
                      hasNextPage
                      hasPreviousPage
                      startCursor
                      endCursor
                    }
                    edges {
                      node {
                        id
                        uuid
                        payDate
                        payer {
                          id
                          uuid
                          name
                        }
                        amount
                        payType
                        receipt
                        isPhotoFee
                      }
                    }
                  }
                }""" % (policyUuid,)
            },
            name="premiumsByPolicies"
        )

    def on_start(self):
        if LEGACY_LOGIN:
            prelogin = self.client.get(
                "/",
                name="prelogin"
            )
            form = {
                **extract_hidden_headers(prelogin.text),
                "hfOfflineHFIDFlag": 0,
                "txtUserName": SITE_USER,
                "txtPassword": SITE_PASSWD,
                "btnLogin": "Login",
            }

            print("encoded:", urlencode(form))
            with self.client.post(
                    "/",
                    data=urlencode(form),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    catch_response=True,
                    name="login"
            ) as response:
                if response.status_code != 200 or "script src=\"/front" not in response.text:
                    print("Failed to login to legacy", response.status_code, response.text)
                    response.failure("Failed to login")
        else:
            self.client.post(
                f"{API_ROOT}/graphql",
                json={"query": """mutation authenticate($username: String!, $password: String!) {
                      tokenAuth(username: $username, password: $password) {
                          refreshExpiresIn
                      }
                      }""", "variables": {"username": SITE_USER, "password": SITE_PASSWD}
                      },
                name="login"
            )


HIDDEN_HEADER_RE = re.compile('<input type="hidden" name="(_.*)" id=".*" value="(.*)" />')


def extract_hidden_headers(html):
    return {x[0]: x[1] for x in HIDDEN_HEADER_RE.findall(html)}


# if launched directly, e.g. "python3 debugging.py", not "locust -f debugging.py"
if __name__ == "__main__":
    run_single_user(SimpleUser)
