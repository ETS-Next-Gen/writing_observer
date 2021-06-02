These Writing Observer modules were folded out of the code when we
were simplifying the UX. These are currently unused. We might fold
these back in at some point, and we should either:

1. Remove them (and restore from version control when needed)
2. Keep them here

Either is fine, but before removing them, it's helpful to
compartmentalize them so we can find them later. Especially `text.js`
is a bit confusing, since we've since also adopted a D3 module called
`text.js`....