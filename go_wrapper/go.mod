module manta_wrapper

go 1.20

require github.com/dotabuff/manta v0.0.0-00010101000000-000000000000

require (
	github.com/davecgh/go-spew v1.1.0 // indirect
	github.com/golang/protobuf v1.5.2 // indirect
	github.com/golang/snappy v0.0.3 // indirect
	google.golang.org/protobuf v1.26.0 // indirect
)

replace github.com/dotabuff/manta => ./manta
