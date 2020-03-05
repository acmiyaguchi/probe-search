import datetime

from mozilla_schema_generator.glean_ping import GleanPing
from peewee import EXCLUDED, chunked, fn

from probe_search.db import Probes, db


def log(message):
    print(
        "{stamp} - {message}".format(
            stamp=datetime.datetime.now().strftime("%x %X"), message=message
        ),
        flush=True,
    )


def import_probes(product):
    log(f"Importing probes for product: {product}")
    log("Fetching probes.")
    probes = GleanPing(product).get_probes()
    log("Gathered {n:,} probes.".format(n=len(probes)))

    log("Batch updating probes to the database.")
    data = []
    for probe in probes:
        definition = probe.definition
        description = definition["description"]

        data.append(
            {
                "product": product,
                "name": probe.name,
                "type": probe.type,
                "description": description,
                "definition": definition,
                "index": fn.to_tsvector("english", " ".join([probe.name, description])),
            }
        )

    with db.atomic():
        for batch in chunked(data, 100):
            (
                Probes.insert_many(batch)
                .on_conflict(
                    conflict_target=[Probes.product, Probes.name],
                    update={
                        Probes.description: EXCLUDED.description,
                        Probes.definition: EXCLUDED.definition,
                        Probes.index: EXCLUDED.index,
                    },
                )
                .execute()
            )
    log("Batch update completed.")


if __name__ == "__main__":
    import_probes("fenix")