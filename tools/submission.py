""""
Data structure to represent student code submissions
"""

class Submission:
    def __init__(
        self, 
        student_id, 
        crid, 
        lab_id, 
        submission_id, 
        type, 
        code, 
        sub_time,
        caption,
        first_name,
        last_name,
        email,
        zip_location,
        submission,
        max_score,
        anomaly_dict=None
    ):
        self.student_id = student_id
        self.crid = crid
        self.lab_id = lab_id
        self.submission_id = submission_id
        self.type = type
        self.code = code
        self.sub_time = sub_time
        self.anomaly_dict = anomaly_dict
        self.caption = caption,
        self.first_name = first_name,
        self.last_name = last_name,
        self.email = email,
        self.zip_location = zip_location,
        self.submission = submission,
        self.max_score = max_score

        # Instantiate public members - these will be set during anomaly processing
        self.num_anomalies = 0
        self.line_count = 0
        self.word_count = 0
        self.num_line_breaks = 0
        self.num_lines_indented = 0
        self.max_var_length = 0
        self.udf_count = 0
        self.udf_list = []
        self.illegal_includes = 0
        self.illegal_includes_list = []
        self.illegal_keywords = 0
        self.illegal_keywords_list = []
        self.illegal_constructs = 0
        self.illegal_constructs_list = []
        self.infloop_count = 0
        self.infloop_list = []
        self.newline_count = 0
        self.has_namespace = False
        self.command_line_args = False
        self.num_comments = 0
        self.single_line_brackets = 0
        self.no_brackets = 0
        self.nulls = 0
        self.scope_operators = 0
        self.endl_count = 0
        self.array_accesses = 0
        self.pointers = 0
        self.ternary_operators = 0
        self.post_operators = 0
        self.const_declarations = 0
        self.upper_case_declarations = 0
        self.camel_case_declarations = 0
        self.lower_case_declarations = 0
        self.no_indentation_in_main = False
        self.same_indentation_in_main = False

        # Dynamically create internal members for the user's regex inputs
        if self.anomaly_dict:
            for k in self.anomaly_dict.keys():
                if 'regex' in k:
                    if self.anomaly_dict[k]['process']:
                        setattr(self, k, 0)
                        setattr(self, k+'_list', [])

        # Private members
        self._anomaly_score = 0
        self._anomalies_print_list = []
        self.__anomaly_computed = False

    def check_if_anomaly_computed(self):
        return self.__anomaly_computed

    def set_anomaly_as_computed(self):
        if not self.__anomaly_computed:
            self.__anomaly_computed = True
    
    def compute_anomaly_score(self):
        """
        When this function is called to compute the anomaly score, we should also populate an internal variable
        that holds a list of all the anomalies that have been found so that we can return this in the student roster
        """
        # User must have passed in the anomaly_dict in order to compute this value.  Raise an error if this isn't present
        if not self.anomaly_dict:
            raise AttributeError("The anomaly_dict object was not set, so we cannot compute the anomaly score")

        # By default assume no anomalies, and therefore no points
        total_points = 0
        self.num_anomalies = 0 # Zero out the number of anomalies in the object before running the computation
        self._anomalies_print_list.clear() # Clear the list of anomalies found before running the computation

        # Styling: identation and line spacing
        PROCESS_INDENT_STYLING = self.anomaly_dict['indent_spacing']['process']
        INDENT_STYLING_POINTS = float(self.anomaly_dict['indent_spacing']['points'])
        
        total_points += PROCESS_INDENT_STYLING * (
            # Instances of minimal indentation/line spacing
            ((1 if self.line_count >= 10 and (self.num_lines_indented < 3 or self.num_line_breaks == 0) else 0) * INDENT_STYLING_POINTS) + 
            # No indentation in main
            (1 if self.no_indentation_in_main else 0 * INDENT_STYLING_POINTS)
        )
        
        self.num_anomalies += PROCESS_INDENT_STYLING * (1 if self.line_count >= 10 and (self.num_lines_indented < 3 or self.num_line_breaks == 0) else 0 + 1 if self.no_indentation_in_main else 0)
        
        if PROCESS_INDENT_STYLING:
            if self.line_count >= 10 and (self.num_lines_indented < 3 or self.num_line_breaks == 0):
                self._anomalies_print_list.append("minimal indentation in code")
            if self.no_indentation_in_main:
                self._anomalies_print_list.append("no indentation in main")

        # Styling: using namespace std;
        PROCESS_NAMESPACE_STD = self.anomaly_dict['namespace_std']['process']
        NAMESPACE_STD_POINTS = float(self.anomaly_dict['namespace_std']['points'])
        
        total_points += PROCESS_NAMESPACE_STD * (1 if not self.has_namespace else 0) * NAMESPACE_STD_POINTS
        self.num_anomalies += PROCESS_NAMESPACE_STD * 1 if not self.has_namespace else 0
        
        if PROCESS_NAMESPACE_STD:
            if not self.has_namespace:
                self._anomalies_print_list.append("using namespace std; not declared")

        # Styling: braces
        PROCESS_BRACES = self.anomaly_dict['brace_styling']['process']
        BRACES_POINTS = float(self.anomaly_dict['brace_styling']['points'])

        total_points += PROCESS_BRACES * (1 if not self.anomaly_dict['brace_styling']['count'] and self.single_line_brackets else self.single_line_brackets) * BRACES_POINTS
        self.num_anomalies += PROCESS_BRACES * self.single_line_brackets

        total_points += PROCESS_BRACES * (1 if not self.anomaly_dict['brace_styling']['count'] and self.no_brackets else self.no_brackets) * BRACES_POINTS
        self.num_anomalies += PROCESS_BRACES * self.no_brackets
        
        if PROCESS_BRACES:
            if self.single_line_brackets:
                self._anomalies_print_list.append("braces on their own line")
            if self.no_brackets:
                self._anomalies_print_list.append("no braces wrapping conditional expr")    

        # Styling: use of \n instead of endl
        PROCESS_NEWLINE = self.anomaly_dict['endl_styling']['process']
        NEWLINE_POINTS = float(self.anomaly_dict['endl_styling']['points'])

        total_points += PROCESS_NEWLINE * (1 if not self.anomaly_dict['endl_styling']['count'] and self.newline_count > 0 and self.endl_count == 0 else (self.newline_count > 0 and self.endl_count == 0) * self.newline_count) * NEWLINE_POINTS
        self.num_anomalies += PROCESS_NEWLINE * (self.newline_count > 0 and self.endl_count == 0) * self.newline_count

        if PROCESS_NEWLINE:
            if self.newline_count > 0 and self.endl_count == 0:
                self._anomalies_print_list.append("use of \\n instead of endl")

        # Atypical includes
        PROCESS_INCLUDES = self.anomaly_dict['atypical_includes']['process']
        INCLUDES_POINTS = float(self.anomaly_dict['atypical_includes']['points'])

        total_points += PROCESS_INCLUDES * (1 if not self.anomaly_dict['atypical_includes']['count'] and self.illegal_includes else self.illegal_includes) * INCLUDES_POINTS
        self.num_anomalies += PROCESS_INCLUDES * self.illegal_includes

        if PROCESS_INCLUDES:
            if self.illegal_includes:
                self._anomalies_print_list.append("atypical includes: " + ", ".join(self.illegal_includes_list))

        # Atypical keywords
        PROCESS_KEYWORDS = self.anomaly_dict['atypical_keywords']['process']
        KEYWORDS_POINTS = float(self.anomaly_dict['atypical_keywords']['points'])

        total_points += PROCESS_KEYWORDS * (1 if not self.anomaly_dict['atypical_keywords']['count'] and self.illegal_keywords else self.illegal_keywords) * KEYWORDS_POINTS
        self.num_anomalies += PROCESS_KEYWORDS * self.illegal_keywords

        if PROCESS_KEYWORDS:
            if self.illegal_keywords:
                self._anomalies_print_list.append("atypical keywords: " + ", ".join(self.illegal_keywords_list))

        # Pointers
        PROCESS_POINTERS = self.anomaly_dict['pointers']['process']
        POINTERS_POINTS = float(self.anomaly_dict['pointers']['points'])

        total_points += PROCESS_POINTERS * (1 if not self.anomaly_dict['pointers']['count'] and self.pointers else self.pointers) * POINTERS_POINTS
        self.num_anomalies += PROCESS_POINTERS * self.pointers

        if PROCESS_POINTERS:
            if self.pointers:
                self._anomalies_print_list.append("pointers declared/used")

        # Array accesses
        PROCESS_ARRAY_ACCESS = self.anomaly_dict['array_accesses']['process']
        ARRAY_ACCESS_POINTS = float(self.anomaly_dict['array_accesses']['points'])

        total_points += PROCESS_ARRAY_ACCESS * (1 if not self.anomaly_dict['array_accesses']['count'] and self.array_accesses else self.array_accesses) * ARRAY_ACCESS_POINTS
        self.num_anomalies += PROCESS_ARRAY_ACCESS * self.array_accesses

        if PROCESS_ARRAY_ACCESS:
            if self.array_accesses:
                self._anomalies_print_list.append("array access ([]) found")

        # Ternary operator
        PROCESS_TERNARY = self.anomaly_dict['ternary_operator']['process']
        TERNARY_POINTS = float(self.anomaly_dict['ternary_operator']['points'])

        total_points += PROCESS_TERNARY * (1 if not self.anomaly_dict['ternary_operator']['count'] and self.ternary_operators else self.ternary_operators) * TERNARY_POINTS
        self.num_anomalies += PROCESS_TERNARY * self.ternary_operators

        if PROCESS_TERNARY:
            if self.ternary_operators:
                self._anomalies_print_list.append("use of ternary (?) operator")

        # Infinite loops
        PROCESS_INFLOOPS = self.anomaly_dict['infinite_loops']['process']
        INFLOOPS_POINTS = float(self.anomaly_dict['infinite_loops']['points'])

        total_points += PROCESS_INFLOOPS * (1 if not self.anomaly_dict['infinite_loops']['count'] and self.infloop_count else self.infloop_count) * INFLOOPS_POINTS
        self.num_anomalies += PROCESS_INFLOOPS * self.infloop_count

        if PROCESS_INFLOOPS:
            if self.infloop_count:
                self._anomalies_print_list.append("inf loop constructs: " + ", ".join(self.infloop_list))

        # UDFs
        PROCESS_UDFS = self.anomaly_dict['udfs']['process']
        UDFS_POINTS = float(self.anomaly_dict['udfs']['points'])

        total_points += PROCESS_UDFS * (1 if not self.anomaly_dict['udfs']['count'] and self.udf_count else self.udf_count) * UDFS_POINTS
        self.num_anomalies += PROCESS_UDFS * self.udf_count

        if PROCESS_UDFS:
            if self.udf_count:
                self._anomalies_print_list.append("user-defined funcs declared/used")

        # CL args
        PROCESS_CL_ARGS = self.anomaly_dict['command_line_args']['process']
        CL_ARGS_POINTS = float(self.anomaly_dict['command_line_args']['points'])

        total_points += PROCESS_CL_ARGS * (1 if not self.anomaly_dict['command_line_args']['count'] and self.command_line_args else self.command_line_args) * CL_ARGS_POINTS
        self.num_anomalies += PROCESS_CL_ARGS * self.command_line_args

        if PROCESS_CL_ARGS:
            if self.command_line_args:
                self._anomalies_print_list.append("int argc, int* argv[] used")

        # Nulls
        PROCESS_NULLS = self.anomaly_dict['nulls']['process']
        NULLS_POINTS = float(self.anomaly_dict['nulls']['points'])

        total_points += PROCESS_NULLS * (1 if not self.anomaly_dict['nulls']['count'] and self.nulls else self.nulls) * NULLS_POINTS
        self.num_anomalies += PROCESS_NULLS * self.nulls

        if PROCESS_NULLS:
            if self.nulls:
                self._anomalies_print_list.append("use of nulls")

        # Scope operator
        PROCESS_SCOPE = self.anomaly_dict['scope_operator']['process']
        SCOPE_POINTS = float(self.anomaly_dict['scope_operator']['points'])

        total_points += PROCESS_SCOPE * (1 if not self.anomaly_dict['scope_operator']['count'] and self.scope_operators else self.scope_operators) * SCOPE_POINTS
        self.num_anomalies += PROCESS_SCOPE * self.scope_operators

        if PROCESS_SCOPE:
            if self.scope_operators:
                self._anomalies_print_list.append("use of :: operator")

        # User provided REGEX
        for regex in self.get_user_regex():
            process = self.anomaly_dict[regex[0]]['process']
            regex_count = getattr(self, regex[0], 0)
            count = self.anomaly_dict[regex[0]]['count']
            points = float(self.anomaly_dict[regex[0]]['points'])
            total_points += process * (1 if not count and regex_count else regex_count) * points 
            self.num_anomalies += process * regex_count

            if process:
                if regex_count:
                    self._anomalies_print_list.append("{}: ".format(regex[0]) + ", ".join(getattr(self, regex[0]+'_list')))
            
        # Set the internal anomaly score member and return
        self._anomaly_score = 1 if total_points >=1 else round(total_points, 2)
        return self._anomaly_score

    @property
    def anomaly_score(self):
        return self._anomaly_score

    @property
    def anomaly_list(self):
        return ", ".join(self._anomalies_print_list)
    
    def set_anomaly_dict(self, anomaly_dict):
        self.anomaly_dict = anomaly_dict

    # Create a list representation of the core object attributes
    def list_representation(self) -> list:
        return [
            self.student_id,
            self.submission_id,
            self.code,
            self.num_anomalies,
            self.anomaly_score,
            self.anomaly_list
        ]

    def get_user_regex(self) -> list:
        return [(key, self.anomaly_dict[key]['expression']) for key in self.anomaly_dict.keys() if 'regex' in key and self.anomaly_dict[key]['process']]