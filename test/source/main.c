
#include <stdio.h>
#include <stdlib.h>

char quote = '"';

const char* empty = "";
const char* wrap_begin = "begin";

#include "bar.h"
#include "test.h"
#include "pragma_once.h"
#include "more/in_nested_dir.h"

const char* wrap_end = "end";

/* " */ #include <more/baz.h> // "

const char* include_foo1 = "#include \"foo.h\"";
const char* include_bar1 = "#include \"bar.h\"";
const char* include_test1 = "\"#include \"test.h\"\"";

const char* include_foo2 = "#include <foo.h>";
const char* include_bar2 = "#include <bar.h>";
const char* include_test2 = "\"#include <test.h>\"";

const char* include_multiple = "\
#include <foo.h> \
#include <bar.h> \
\"#include <test.h>\" \
";

const char* include_concat = """#include <foo.h>";

int main(int argc, char* argv[])
{
	(void)argc;
	printf("%s\n", argv[0]);
	assert(foo() == 1);
	assert(bar() == 2);
	return EXIT_SUCCESS;
}

