from neo4j import GraphDatabase


class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query(self, cypher_query, parameters=None):
        with self.driver.session() as session:
            result = session.run(cypher_query, parameters)
            return [record.data() for record in result]


# 连接配置
URI = "neo4j+s://d0da9c00.databases.neo4j.io"  # 替换为你的 GCP Neo4j 地址
USER = "neo4j"  # 默认用户名
PASSWORD = "if-1b7h7hV-stFoCNOrCliBlc4AM-rEyrn9gEomG-Yk"  # 替换为你的密码

# 创建连接
conn = Neo4jConnection(URI, USER, PASSWORD)

try:
    # # 测试查询：获取数据库信息
    result = conn.query("RETURN 'Connection successful!' as message")
    print(result)
    #
    # all_related = conn.query("""
    #     MATCH (zhangsan:Person {name: '张三'})-[r]-(related)
    #     RETURN type(r) as relationship, labels(related) as labels, related.name as name
    # """)
    # print("张三的所有直接关系:", all_related)
    #
    # # 方法2：分别获取朋友和技能
    # friends_and_skills = conn.query("""
    #     MATCH (zhangsan:Person {name: '张三'})-[:FRIEND]->(friend:Person)
    #     RETURN 'FRIEND' as type, friend.name as name, friend.age as age, null as skill
    #     UNION
    #     MATCH (zhangsan:Person {name: '张三'})-[:KNOWS]->(skill:Skill)
    #     RETURN 'SKILL' as type, skill.name as name, null as age, skill.name as skill
    # """)
    # print("张三的朋友和技能:", friends_and_skills)
    #
    # # 方法3：获取更详细的信息（包括关系类型）
    # detailed = conn.query("""
    #     MATCH (zhangsan:Person {name: '张三'})-[r]->(node)
    #     RETURN
    #         type(r) as relationship_type,
    #         labels(node)[0] as node_type,
    #         properties(node) as properties
    # """)
    # print("详细信息:", detailed)
    #
    # # 方法4：如果要遍历多度关系（比如朋友的朋友）
    # multi_degree = conn.query("""
    #     MATCH path = (zhangsan:Person {name: '张三'})-[*1..2]-(related)
    #     RETURN DISTINCT
    #         labels(related)[0] as type,
    #         related.name as name,
    #         length(path) as distance
    #     ORDER BY distance
    # """)
    # print("多度关系（1-2度）:", multi_degree)
    # conn.query("""
    #     MATCH (wangwu:Person {name: '王五'})
    #     MATCH (zhaoliu:Person {name: '赵六'})
    #     CREATE (wangwu)-[:FRIEND]->(zhaoliu)
    #     CREATE (zhaoliu)-[:FRIEND]->(wangwu)
    # """)
    #
    # print("王五和赵六的朋友关系已创建！")
    #
    # # 验证：查询王五的朋友
    # wangwu_friends = conn.query("""
    #     MATCH (wangwu:Person {name: '王五'})-[:FRIEND]->(friend:Person)
    #     RETURN friend.name as name, friend.age as age
    # """)
    # print("王五的朋友:", wangwu_friends)
    # conn.query("""
    #     MATCH (zhangsan:Person {name: '张三'})
    #     SET zhangsan.birthday = '2000-02-22',
    #         zhangsan.city = '北京'
    # """)
    #
    # # 更新李四的属性
    # conn.query("""
    #     MATCH (lisi:Person {name: '李四'})
    #     SET lisi.birthday = '2001-05-03',
    #         lisi.city = '上海'
    # """)
    #
    # # 更新王五的属性
    # conn.query("""
    #     MATCH (wangwu:Person {name: '王五'})
    #     SET wangwu.birthday = '2003-05-06',
    #         wangwu.city = '杭州'
    # """)
    #
    # print("属性更新成功！")
    #
    # # 验证：查询所有人的完整信息
    # people = conn.query("""
    #     MATCH (p:Person)
    #     RETURN p.name as name, p.age as age, p.birthday as birthday, p.city as city
    #     ORDER BY p.name
    # """)
    # print("所有人物信息:", people)



    # network = conn.query("""
    #     MATCH (zhangsan:Person {name: '张三'})-[r1]-(related)
    #     OPTIONAL MATCH (related)-[r2]-(other)
    #     WHERE other <> zhangsan
    #     RETURN DISTINCT
    #         zhangsan.name as center,
    #         type(r1) as relationship1,
    #         labels(related)[0] as related_type,
    #         related.name as related_name,
    #         type(r2) as relationship2,
    #         labels(other)[0] as other_type,
    #         other.name as other_name
    # """)
    # print("张三的关系网络:", network)


    # # 创建刑法和婚姻法节点
    # conn.query("""
    #     CREATE (xingfa:LawType {name: '刑法'})
    #     CREATE (hunyinfa:LawType {name: '婚姻法'})
    # """)
    #
    # # 建立法律与刑法、婚姻法的关系
    # conn.query("""
    #     MATCH (law:Skill {name: '法律'})
    #     MATCH (xingfa:LawType {name: '刑法'})
    #     MATCH (hunyinfa:LawType {name: '婚姻法'})
    #     CREATE (law)-[:INCLUDES]->(xingfa)
    #     CREATE (law)-[:INCLUDES]->(hunyinfa)
    # """)
    #
    # print("法律细分添加成功！")
    #
    # # 验证：查询法律相关的所有节点
    # law_details = conn.query("""
    #     MATCH (zhangsan:Person {name: '张三'})-[:KNOWS]->(law:Skill {name: '法律'})-[:INCLUDES]->(lawtype)
    #     RETURN
    #         zhangsan.name as person,
    #         law.name as skill,
    #         collect(lawtype.name) as law_types
    # """)
    # print("张三的法律技能详情:", law_details)
    #
    # # 查看完整的关系链
    # full_chain = conn.query("""
    #     MATCH path = (zhangsan:Person {name: '张三'})-[:KNOWS]->(law:Skill {name: '法律'})-[:INCLUDES]->(lawtype)
    #     RETURN
    #         zhangsan.name as person,
    #         law.name as skill,
    #         lawtype.name as law_type
    # """)
    # print("完整关系链:", full_chain)

    network = conn.query("""
            MATCH (zhangsan:Person {name: '张三'})-[r1]-(related)
            OPTIONAL MATCH (related)-[r2]-(other)
            WHERE other <> zhangsan
            RETURN DISTINCT
                zhangsan.name as center,
                properties(zhangsan) as center_props,
                type(r1) as relationship1,
                labels(related)[0] as related_type,
                related.name as related_name,
                properties(related) as related_props,
                type(r2) as relationship2,
                labels(other)[0] as other_type,
                other.name as other_name,
                properties(other) as other_props
        """)
    print("张三的关系网络（含属性）:", network)


finally:
    conn.close()