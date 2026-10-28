from sqlalchemy import event

from app.services import task_service


def test_list_tasks_loads_tags_in_fixed_number_of_queries(db_session):
    # 할 일 5개를 태그와 함께 만듭니다.
    for i in range(5):
        task_service.create_task(db_session, f"할 일 {i}", ["개인", f"태그{i}"])
    # identity map을 비워 아래 조회가 DB에서 다시 읽히도록 합니다.
    db_session.expunge_all()

    statements = []

    def count_statement(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", count_statement)
    try:
        tasks = task_service.list_tasks(db_session)
        # 태그에 접근해야 지연 로딩이 일어나므로 함께 실행합니다.
        for task in tasks:
            _ = [tag.name for tag in task.tags]
    finally:
        event.remove(engine, "before_cursor_execute", count_statement)

    assert len(tasks) == 5
    # 할 일 조회 1회 + 태그 IN 조회 1회. N+1이면 6회 이상이 됩니다.
    assert len(statements) == 2
