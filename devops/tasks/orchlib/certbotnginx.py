'''
This is a utility which allows us to remove the certbot sections of
an nginx config file.

It will remove lines with `ssl` and `certbot` in them, and the
second server section (which is the port 80 redirect), and change
port 443 (SSL) back to 80.

It's not 100% a reversion. For a typical config file, it's correct,
but it will change newlines at the end, remove a comment mentioning
certbot, and flip around port 80 and port [::]:80 relative to the
pre-certbot version. But it's functionally identical.

It will also not work for files which follow a very different
pattern. For example, we really should introspect the `server`
section and remove the redirect specifically. But this is good
enough.

We do use a proper parser, though!
'''

from ply import lex, yacc


class NginxParser:
    '''
    pyl parser for nginx files, with some added functionality for
    modifying them
    '''
    tokens = (
        'CONTENT',
        'SEMICOLON',
        'LBRACE',
        'RBRACE',
    )

    t_SEMICOLON = r';'
    t_LBRACE = r'{'
    t_RBRACE = r'}'

    # If we wanted to ignore whitespace, we'd include:
    # t_ignore = ' \t\n'
    # However, we'd like to write this back out with whitespace.

    def t_CONTENT(self, t):
        r'[^{};]+'
        return t

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}'")
        t.lexer.skip(1)

    def __init__(
            self,
            exclude_strings=None,
            replacements=None,
            remove_nth_server=None
    ):
        self.exclude_strings = exclude_strings or []
        self.replacements = replacements or {}
        self.remove_nth_server = remove_nth_server
        self.server_count = 0
        self.lexer = lex.lex(module=self)

    def p_config(self, p):
        '''config : items'''
        p[0] = p[1]

    def p_items(self, p):
        '''items : item
                 | items item'''
        if len(p) == 2:
            p[0] = [p[1]] if p[1] is not None else []
        else:
            p[0] = p[1] + ([p[2]] if p[2] is not None else [])

    def p_item(self, p):
        '''item : statement
                | block'''
        p[0] = p[1]

    def p_statement(self, p):
        '''statement : CONTENT SEMICOLON
                     | CONTENT'''
        content = p[1]
        for old, new in self.replacements.items():
            content = content.replace(old, new)

        if any(exclude in content for exclude in self.exclude_strings):
            p[0] = None
        elif len(p) == 3:
            p[0] = content + p[2]
        else:
            p[0] = content

    def p_block(self, p):
        '''block : CONTENT LBRACE items RBRACE
                 | LBRACE items RBRACE'''
        if len(p) == 5:
            content = p[1]
            items = p[3]
            if content.strip().startswith('server'):
                self.server_count += 1
                if self.server_count == self.remove_nth_server:
                    p[0] = None
                    return
        else:
            content = ''
            items = p[2]

        for old, new in self.replacements.items():
            content = content.replace(old, new)

        if any(exclude in content for exclude in self.exclude_strings):
            p[0] = None
        elif len(p) == 5:
            p[0] = [content, p[2], items, p[4]]
        else:
            p[0] = [p[1], items, p[3]]

    def p_error(self, p):
        print(f"Syntax error at '{p.value}'")


def parse_nginx_config(
        config_string,
        exclude_strings=None,
        replacements=None,
        remove_nth_server=None
):
    '''
    Function to parse an nginx config string with filtering. We can:

    * Remove lines which match a set of strings (e.g. all lines with `ssl`)
    * Replace strings (e.g. 443 -> 80)
    * Remove server sections
    '''
    nginx_parser = NginxParser(
        exclude_strings, replacements, remove_nth_server
    )
    parser = yacc.yacc(module=nginx_parser)
    return parser.parse(config_string, lexer=nginx_parser.lexer)


def nginx_parse_to_string(parsed_config):
    '''
    Function to convert the config parse tree back to a string
    '''
    output = []
    for item in parsed_config:
        if isinstance(item, list):  # This is a block
            if len(item) == 4:  # Block with content before brace
                output.append(item[0] + item[1])
                output.extend(nginx_parse_to_string(item[2]))
                output.append(item[3])
            else:  # Block without content before brace
                output.append(item[0])
                output.extend(nginx_parse_to_string(item[1]))
                output.append(item[2])
        else:  # This is a statement
            output.append(item)
    return ''.join(output)


def strip_nginx(config_string):
    '''
    This is the main function of the program. Read in an nginx
    file, remove the certbot strings, and write it back out.
    '''
    parsed = parse_nginx_config(
        config_string,
        exclude_strings=['ssl', 'certbot'],
        replacements={'443': '80'},
        remove_nth_server=2
    )

    written = nginx_parse_to_string(parsed)
    return written


TEST_CONFIG = """
server {
   server_name example.learning-observer.org;

   location ~ /static/repos/server/example_problems/.*/videos/ {
      rewrite /static/repos/server/example_problems/.*/videos/(.*)$ /videos/$1;
   }

   location /videos {
      root /home/ubuntu/example/problems/;
   }

   location /example-hook/ {
      root /home/ubuntu/example/;
      include /etc/nginx/fastcgi_params;
      fastcgi_pass   unix:/var/run/fcgiwrap.socket;
      fastcgi_param  SCRIPT_FILENAME   /home/ubuntu/example/update;
   }

   location / {
      # Generally, used to configure permissions. E.g. http basic
      # auth, allow/deny IP blocks, etc. Note that for deploy, this
      # should be broken out into several blocks (e.g. incoming event,
      # dashboards, etc.)

      proxy_pass http://localhost:8888/;
          proxy_set_header   X-Real-IP       $remote_addr;
          proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;

   }

   location /wsapi/ {
      proxy_pass http://localhost:8888/wsapi/;
      proxy_set_header        X-Real-IP       $remote_addr;
      proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_read_timeout 86400;

      if ($request_method = OPTIONS ) {
         return 200;
      }
    }

    listen [::]:80;
    listen 80;

}server {
    if ($host = example.learning-observer.org) {
        return 301 https://$host$request_uri;
    } # managed by Certbot



   server_name example.learning-observer.org;

    listen 80;
    listen [::]:80;
    return 404; # managed by Certbot

}

"""

# Example usage / test case
if __name__ == '__main__':
    stripped = strip_nginx(TEST_CONFIG)
    print(stripped)
