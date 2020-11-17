# This is a helper script, so we run code quality checks with the same
# parameters.

# All code SHOULD conform to PEP8, except for line length
# limitations. We may re-examine this decision once we have sufficient
# developers working on VT100 terminals.
#
# See: https://lkml.org/lkml/2020/5/29/1038

echo "============"
echo "Issues"
echo "============"

pycodestyle --ignore=E501 *py

echo "============"
echo "Yellow flags"
echo "============"

# We should still break lines where convenient. But 80 characters
# breaks down even for things as simple as AJAX URLs

pycodestyle *py

# And we don't mind many pylint issues, but it's helpful for finding
# style issues too

pylint *py
