import os           # Generic imports
import pytest, warnings  # For testing 
import shapely.wkt      # For comparing wkt's

from helpers import make_request, request_to_json

class test_files_to_wkt():
    def __init__(self, test_info):
        if "api" not in cli_args:
            assert False, "Endpoint test ran, but '--api' not declared in CLI. (test_files_to_wkt)"
        # Join the url 'start' to the endpoint, even if they both/neither have '/' between them:
        url_parts = [cli_args["api"], "services/utils/files_to_wkt"]
        cli_args["api"] = '/'.join(s.strip('/') for s in url_parts)
        test_info = self.applyDefaultValues(test_info)
    
    def applyDefaultValues(self, test_info):
        # Figure out what test is 'expected' to do:
        pass_assertions = ["parsed wkt"]
        fail_assertions = ["parsed error msg"]
        # True if at least one of the above is used, False otherwise:
        test_info["asserts pass"] = 0 != len([k for k,_ in test_info.items() if k in pass_assertions])
        test_info["asserts fail"] = 0 != len([k for k,_ in test_info.items() if k in fail_assertions])

        # Default Print the result to screen if tester isn't asserting anything. Else just run the test:
        if "print" not in test_info:
            test_info["print"] = False if "parsed wkt" in test_info or "parsed error msg" in test_info else True

        if not isinstance(test_info["file wkt"], type([])):
            test_info["file wkt"] = [ test_info["file wkt"] ]

        resources_dir = os.path.join(os.path.realpath(os.path.dirname(__file__)), "Resources")
        files_that_exist = []
        for file in test_info["file wkt"]:
            file_path = os.path.join(resources_dir, file)
            if os.path.isfile(file_path):
                # Save it in the format the api is expecting:
                files_that_exist.append(('files', open(file_path, 'rb')))
            else:
                assert False, "File not found: {0}. File paths start after: '{1}'. (Test: '{2}')".format(file_path, resources_dir, test_info["title"])
        # Override with the new files:
        test_info["file wkt"] = files_that_exist
        return test_info






class test_repair_wkt():
    def __init__(self, test_info, file_conf, cli_args):
        if "api" not in cli_args or cli_args["api"] == None:
            assert False, "Endpoint test ran, but '--api' not declared in CLI. (test_repair_wkt)"
        # Join the url 'start' to the endpoint, even if they both/neither have '/' between them:
        url_parts = [ cli_args["api"], "services/utils/wkt" ]
        full_url = '/'.join(s.strip('/') for s in url_parts)
        test_info = self.applyDefaultValues(test_info)
        # Make a request, and turn it into json. Helpers should handle if something goes wrong:
        response_server = make_request(full_url, data={"wkt": test_info["test wkt"]} ).content.decode("utf-8")
        response_json = request_to_json(response_server, full_url, test_info["title"]) # The last two params are just for helpfull error messages
        # Make sure the response matches what is expected from the test:
        self.runAssertTests(test_info, response_json)

    def applyDefaultValues(self, test_info):
        # Copy 'repaired wkt' to the wrapped/unwrapped versions if used:
        if "repaired wkt" in test_info:
            for i in ["repaired wkt wrapped", "repaired wkt unwrapped"]:
                if i not in test_info:
                    test_info[i] = test_info["repaired wkt"]
            del test_info["repaired wkt"]
    
        # Figure out what test is 'expected' to do:
        pass_assertions = ["repaired wkt wrapped", "repaired wkt unwrapped", "repair"]
        fail_assertions = ["repaired error msg"]
        # True if at least one of the above is used, False otherwise:
        pass_assertions_used = 0 != len([k for k,_ in test_info.items() if k in pass_assertions])
        fail_assertions_used = 0 != len([k for k,_ in test_info.items() if k in fail_assertions])

        # Default Print the result to screen if tester isn't asserting anything:
        if "print" not in test_info:
            test_info["print"] = False if (pass_assertions_used or fail_assertions_used) else True
        if "check repair" not in test_info:
            repair_if_used = ["repaired wkt wrapped", "repaired wkt unwrapped", "repair"]
            if len([k for k,_ in test_info.items() if k in repair_if_used]) > 0:
                test_info["check repair"] = True
            else:
                test_info["check repair"] = False

        # Add the repair if needed. Make sure it's a list:
        if "repair" not in test_info:
            test_info["repair"] = []
        elif not isinstance(test_info["repair"], type([])):
            test_info["repair"] = [test_info["repair"]]
        
        # If they passed more than one wkt, combine them:
        if isinstance(test_info["test wkt"], type([])):
            test_info["test wkt"] = "GEOMETRYCOLLECTION({0})".format(",".join(test_info['test wkt']))
        return test_info

    def runAssertTests(self, test_info, response_json):
        if "repaired wkt wrapped" in test_info:
            if "wkt" in response_json:
                assert shapely.wkt.loads(response_json["wkt"]["wrapped"]) == shapely.wkt.loads(test_info["repaired wkt wrapped"]), "WKT wrapped failed to match the result. Test: '{0}'\nExpected: {1}\nActual: {2}\n".format(test_info["title"], test_info["repaired wkt wrapped"], response_json["wkt"]["wrapped"])
            else:
                assert False, "WKT not found in response from API. Test: '{0}'. Response: {1}.".format(test_info["title"], response_json)
        if "repaired wkt unwrapped" in test_info:
            if "wkt" in response_json:
                assert shapely.wkt.loads(response_json["wkt"]["unwrapped"]) == shapely.wkt.loads(test_info["repaired wkt unwrapped"]), "WKT unwrapped failed to match the result. Test: '{0}'\nExpected: {1}\nActual: {2}\n".format(test_info["title"], test_info["repaired wkt wrapped"], response_json["wkt"]["wrapped"])
            else:
                assert False, "WKT not found in response from API. Test: '{0}'. Response: {1}.".format(test_info["title"], response_json)

        if test_info["check repair"]:
            if "repairs" in response_json:
                for repair in test_info["repair"]:
                    assert repair in str(response_json["repairs"]), "Expected repair was not found in results. Test: '{0}'. Repairs done: {1}".format(test_info["title"], response_json["repairs"])
                assert len(response_json["repairs"]) == len(test_info["repair"]), "Number of repairs doesn't equal number of repaired repairs. Test: '{0}'. Repairs done: {1}.".format(test_info["title"],response_json["repairs"])
            else:
                assert False, "Unexpected WKT returned: {0}. Test: '{1}'".format(response_json, test_info["title"])
        if "repaired error msg" in test_info:
            if "error" in response_json:
                assert test_info["repaired error msg"] in response_json["error"]["report"], "Got different error message than expected. Test: '{0}'.\nError returned: {1}".format(test_info["title"], response_json["error"]["report"])
            else:
                assert False, "Unexpected WKT returned: {0}. Test: '{1}'\nResponse: {2}.".format(response_json, test_info["title"], response_json)

