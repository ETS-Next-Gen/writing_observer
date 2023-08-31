import learning_observer.module_loader


def check_integration(module, id):
    for item in module.REDUCERS:
        reducer_id = f'{id}.{item["function"].__name__}'
        assert item.items() <= next(x for x in learning_observer.module_loader.reducers() if x['id'] == reducer_id).items()

    assert module.EXECUTION_DAG.items() <= learning_observer.module_loader.execution_dags()[id].items()
