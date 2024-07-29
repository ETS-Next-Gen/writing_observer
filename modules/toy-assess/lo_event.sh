rm -Rf .next/cache/
pushd ../lo_event/
npm run prebuild
npm pack
popd
npm install ../lo_event/lo_event-0.0.2.tgz  --no-save
