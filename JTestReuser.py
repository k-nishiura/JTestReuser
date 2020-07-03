import javalang, sys, os, csv, random
from pathlib import Path
import numpy as np

From = "springside4"
To = "SimianArmy"

Object_methods = "clone equals finalize getClass hashcode notify notifyAll toString wait".split()
class Project():
    def __init__(self, path):
        self.path = path
        self.products = self.expandExtends(self.getProductMethods())
        self.testhelpers = self.expandExtends(self.getTestHelperMethods())
        self.tests = self.getTestMethods(path)

    def getProductMethods(self):
        path = self.path
        javas = list(Path(path).glob("**/*.java"))
        products = [i for i in javas if "/test/" not in str(i)]

        ClassList = []
        for codepath in products:
            try:
                code = codepath.open()
                strcode = " ".join([i for i in code])
                tree = javalang.parse.parse(strcode)
                code.close()
            except:
                print("error:", str(path))
            else:
                _class = []
                for cls in tree.types:
                    if str(type(cls))=="<class 'javalang.tree.ClassDeclaration'>":
                        _class.append(cls)
                while(_class):
                    cls = _class.pop(0)

                    ThisClass = Class(cls.name)
                    ThisClass.obj, ThisClass.path = cls, codepath

                    Members, Methods, Constructors = [], [], []
                    for c in cls.body:
                        if str(type(c))=="<class 'javalang.tree.ClassDeclaration'>":
                            _class.append(c)
                        elif str(type(c))=="<class 'javalang.tree.FieldDeclaration'>":
                            if "private" not in c.modifiers:
                                Members.append(c)
                        elif str(type(c))=="<class 'javalang.tree.MethodDeclaration'>":
                            if "private" not in c.modifiers:
                                Methods.append(c)
                        elif str(type(c))=="<class 'javalang.tree.ConstructorDeclaration'>":
                            Constructors.append(c)
                    ThisClass.members, ThisClass.methods, ThisClass.constructors = Members, Methods, Constructors
                    ClassList.append(ThisClass)
        return ClassList

    def getTestHelperMethods(self):
        path = self.path
        javas = list(Path(path).glob("**/*.java"))
        tests = [i for i in javas if "/test/" in str(i)]

        ClassList = []
        for codepath in tests:
            try:
                code = codepath.open()
                strcode = " ".join([i for i in code])
                tree = javalang.parse.parse(strcode)
                code.close()
            except:
                print("error:", str(path))
            else:
                _class = []
                for cls in tree.types:
                    if str(type(cls))=="<class 'javalang.tree.ClassDeclaration'>":
                        _class.append(cls)
                while(_class):
                    cls = _class.pop(0)

                    ThisClass = Class(cls.name)
                    ThisClass.obj, ThisClass.path = cls, codepath

                    Members, Methods, Constructors = [], [], []
                    for c in cls.body:
                        if str(type(c))=="<class 'javalang.tree.ClassDeclaration'>":
                            _class.append(c)
                        elif str(type(c))=="<class 'javalang.tree.FieldDeclaration'>":
                            if "private" not in c.modifiers:
                                Members.append(c)
                        elif str(type(c))=="<class 'javalang.tree.MethodDeclaration'>":
                            if "Test" not in [i.name for i in c.annotations]:
                                Methods.append(c)
                        elif str(type(c))=="<class 'javalang.tree.ConstructorDeclaration'>":
                            Constructors.append(c)
                    ThisClass.members, ThisClass.methods, ThisClass.constructors = Members, Methods, Constructors
                    ClassList.append(ThisClass)
        return ClassList

    def expandExtends(self, ClassList):
        namelist = [c.name for c in ClassList]
        name2list ={}
        extendsFrom = {}
        for c in ClassList:
            name2list[c.name] = c
        for c in ClassList:
            try:
                extendsFrom[c.name] = name2list[c.obj.extends.name]
            except:
                pass

        change = 1
        while(change):
            change = 0
            tmp = []
            for c in ClassList:
                try:
                    e = extendsFrom[c.name]
                    c_name = [i.name for i in c.methods]
                    for m in e.methods:
                        if m.name not in c_name:
                            c.methods.append(m)
                            change+=1
                except:
                    pass
                tmp.append(c)
            ClassList = tmp
        return ClassList

    def getTestMethods(self, path):
        javas = list(Path(path).glob("**/*.java"))
        tests = [i for i in javas if "/test/" in str(i)]

        TestMethodList = []
        for codepath in tests:
            #print(codepath.stem)
            try:
                code = codepath.open()
                strcode = " ".join([i for i in code])
                tree = javalang.parse.parse(strcode)
                code.close()
            except:
                print("error:", str(path))
            else:
                _methods = []
                for cls in tree.types:
                    if str(type(cls))=="<class 'javalang.tree.ClassDeclaration'>":
                        if cls.extends is None and "abstruct" not in cls.modifiers:
                            before, after = [], []
                            for c in cls.body:
                                if str(type(c))=="<class 'javalang.tree.MethodDeclaration'>":
                                    if "Before" in [i.name for i in c.annotations]:
                                        before.append(c)
                                    elif "After" in [i.name for i in c.annotations]:
                                        after.append(c)
                            for c in cls.body:
                                if str(type(c))=="<class 'javalang.tree.MethodDeclaration'>":
                                    if "Test" in [i.name for i in c.annotations]:
                                        #print("   ", c.name)
                                        tc = TestCase(c.name)
                                        tc.path, tc.c_obj, tc.m_obj = codepath, cls, c
                                        tc.before, tc.after = before, after
                                        tc.call = Call(self)
                                        TestMethodList.append(tc)
                #TestMethodList.append(_methods)
        return TestMethodList

    def getCobj(self, cname):
        for c in self.products + self.testhelpers:
            if c.name == cname:
                return c.obj

    def SearchBox(self, ClassList, cname, mname, nargs):
        results = []
        for c in ClassList:
            if c.name == cname:
                for m in c.methods+c.constructors:
                    if m.name == mname:
                        if len(m.parameters) == nargs:
                            results.append(m)
                        elif len(m.parameters) == 1:
                            if m.parameters[0].varargs == True:
                                results.append(m)
        return [len(results), results]

    def allExtractCall(self):
        TestMethods = self.tests
        for t in TestMethods:
            self.extractCall(t)

    def extractCall(self, TestMethod):
        c_obj, m_obj = TestMethod.c_obj, TestMethod.m_obj
        Products, TestHelpers = self.products, self.testhelpers
        Both = Products + TestHelpers

        call = Call(self)
        CalledProducts = []
        CalledTestHelpers = []
        CalledUnknowns = Class("Unknown")

        #全ての固有クラス名
        AllSpecificClasses = [i.name for i in Both]
        AllProductClassName = [i.name for i in Products]
        AllTestHelperClassName = [i.name for i in TestHelpers]
        #全ての固有メソッド名・メンバ名
        AllSpecificMethods = []
        AllSpecificMembers = []
        for c in Products+TestHelpers:
            AllSpecificMethods.extend([i.name for i in c.methods])
            AllSpecificMembers.extend([i.declarators[0].name for i in c.members])
        AllSpecificMethodName = set(AllSpecificMethods)
        AllSpecificMemberName = set(AllSpecificMembers)
        #同じクラスのメソッド名
        SameClassMethods = []
        for c in TestHelpers:
            if c.name == c_obj.name:
                SameClassMethods = [i.name for i in c.methods]
                break

        #===========================================================================
        #print("    変数定義抽出")
        variables = {}
        for s in c_obj:
            if str(type(s[1])) == "<class 'javalang.tree.FieldDeclaration'>":
                variables[s[1].declarators[0].name] = s[1].type.name
        for s in m_obj:
            if str(type(s[1])) == "<class 'javalang.tree.LocalVariableDeclaration'>":
                if s[1].type.name in AllSpecificClasses:
                    variables[s[1].declarators[0].name] = s[1].type.name
            if str(type(s[1])) == "<class 'javalang.tree.FormalParameter'>":
                if s[1].type.name in AllSpecificClasses:
                    variables[s[1].name] = s[1].type.name
            if str(type(s[1])) == "<class 'javalang.tree.TryResource'>":
                if s[1].type.name in AllSpecificClasses:
                    variables[s[1].name] = s[1].type.name
        #print("        変数:", [i for i in variables])


        #===========================================================================
        #print("    固有型抽出")
        ClassNames = [variables[i] for i in variables]
        for s in m_obj:
            if str(type(s[1])) == "<class 'javalang.tree.ReferenceType'>":
                if s[1].name in AllSpecificClasses:
                    ClassNames.append(s[1].name)

        for c in list(set(ClassNames)):
            call.addClass(c)


        #===========================================================================
        #print("    固有クラスのメンバへのアクセス")

        def search_member(_class, _member):
            #return [cname, _member, type, obj]
            cname, _type, obj = None, None, None

            if _class is None:
                return None

            if _class == "":
                return None

            if _member not in AllSpecificMembers:
                return None

            if "." in _class:
                m = _class.split(".")[-1]
                c = ".".join(_class.split(".")[:-1])
                result = search_member(c,m)
                if result is None:
                    return None
                #call.append("members", result[:-1], res, result[-1])
                cname = result[2]
                if cname not in AllSpecificClasses:
                    return None
            else:
                if _class[0].isupper():
                    if _class in AllSpecificClasses:
                        cname = _class
                    else:
                        return None
                else:
                    if _class in variables:
                        cname = variables[_class]
                    else:
                        cname = "(Unknown)"

            for c in self.products + self.testhelpers:
                if c.name == cname:
                    for m in c.members:
                        if m.declarators[0].name == _member:
                            obj = m
                            _type = m.type.name
                            break

            call.append("members", [cname, _member, 0], [False, False], obj)
            return [cname, _member, _type, obj]

        for s in m_obj:
            if str(type(s[1])) == "<class 'javalang.tree.MemberReference'>":
                cname = s[1].qualifier
                member = s[1].member
                obj = None
                searched = search_member(cname, member)

                #cnameとして考えられるのは4種類
                #1 ""　これはメンバではない
                #2 クラス名　クラスを直接検索
                #3 変数名　変数名からクラスを辿って検索
                #4 (クラス/変数).メンバ　これ自体がメンバなので再起的に登録する必要がある


        #===========================================================================
        #メソッド・クラス生成
        done = []
        before = "(Unknown)"
        for s in m_obj:
            now = str(before)
            before = "(Unknown)"

            if str(type(s[1])) == "<class 'javalang.tree.MethodInvocation'>":
                q = s[1].qualifier
                mname = s[1].member
                nargs = len(s[1].arguments)

                #---------------------------------------------------------フィルタリング
                #固有メソッドリストにないものは除外
                if mname not in AllSpecificMethods:
                    continue
                #オブジェクトメソッドは除外
                if mname in Object_methods:
                    continue
                #一回見たことあるやつは除外
                if str(q)+"/"+mname+"/"+str(nargs) in done:
                    continue
                done.append(str(q)+"/"+mname+"/"+str(nargs))


                #---------------------------------------------------------クラス名の特定
                #cname（クラス名）, mname（メソッド名）, nargs（引数数）を収集
                if q is None:
                    #前のメソッドのメソッドチェーン
                    #　一つ前のメソッドorクラス生成文のreturn型を参照
                    if before in AllSpecificClasses:
                        cname = before
                    else:
                        continue
                elif q == "":
                    #同じクラス内のメソッド
                    #static importしたメソッド
                    if mname in SameClassMethods:
                        cname = c_obj.name
                    else:
                        cname = "(Unknown)"
                elif "." in q:
                    q1, q2 = ".".join(q.split(".")[:-1]), q.split(".")[-1]
                    r = search_member(q1, q2)
                    if r is not None:
                        cname = r[2]
                        if cname not in AllSpecificClasses:
                            continue
                elif q[0].isupper():
                    #クラス.メソッド
                    if q in AllSpecificClasses:
                        cname = q
                    else:
                        continue
                else:
                    #変数.メソッド
                    try:
                        cname = variables[q]
                    except:
                        cname = "(Unknown)"


                #---------------------------------------------------------クエリを発行
                result = self.SearchBox(Both, cname, mname, nargs)
                obj = None
                unique = False
                exist = False
                if result[0] == 1:
                    obj = result[1][0]
                    unique = exist = True
                elif result[0] > 1:
                    obj = result[1][0]
                    exist = True
                query = [cname, mname, nargs]
                resultset = [exist, unique]

                if obj is not None:
                    before = obj.return_type.name if obj.return_type is not None else ""

                #---------------------------------------------------------Callオブジェクトへ格納
                call.append("methods",query,resultset, obj)


            #---------------------------------------------------------コンストラクタ抽出
            if str(type(s[1])) == "<class 'javalang.tree.ClassCreator'>":
                cname = s[1].type.name
                nargs = len(s[1].arguments)
                if cname not in AllSpecificClasses:
                    continue
                if cname+"/"+str(nargs) in done:
                    continue
                done.append(cname+"/"+str(nargs))
                before = cname

                query = [cname, cname, nargs]
                #resultset = [True, True]
                exist, unique = False, False
                obj = None

                result = self.SearchBox(Both, cname, cname, nargs)
                if result[0] > 0:
                    exist = True
                    obj = result[1][0]
                    if result[0] == 1:
                        unique = True
                else:
                    if nargs == 0:
                        continue

                resultset = [exist, unique]
                call.append("constructors", query, resultset, obj)


        #===========================================================================
        #TestMethod.call = [CalledProducts, CalledTestHelpers, CalledUnknowns]
        TestMethod.call = call
        return TestMethod

class Class():
    def __init__(self, name):
        self.name = name
        self.path = None
        self.id = None
        self.obj = None
        self.members = []
        self.methods = []
        self.constructors = []

class TestCase():
    def __init__(self, name):
        self.name = name
        self.path = None
        self.m_obj = None
        self.c_obj = None
        self.before = []
        self.after = []
        self.call = None

    def print(self):
        print(self.path)
        print("抽出結果:")
        #CalledProducts, CalledTestHelpers, CalledUnknowns = self.call
        CalledProducts, CalledTestHelpers, CalledUnknowns = self.call.products, self.call.testhelpers, self.call.unknown
        warning = len(CalledUnknowns.members)+len(CalledUnknowns.methods)+len(CalledUnknowns.constructors)
        existUnknown = bool(warning)
        print("    Products:", len(CalledProducts), "TestHelpers:",len(CalledTestHelpers), "Unknown:", existUnknown)
        category = ["[Products]:", "[TestHelpers]:", "[Unknown]:"]
        Calls = [CalledProducts, CalledTestHelpers, [CalledUnknowns]]
        for name, _list in zip(category, Calls):
            print(name)
            if name == "[Unknown]:" and existUnknown == False:
                continue
            for p in _list:
                print("   ", p.name)
                print("   ","    メンバ:", len(p.members))
                for m in p.members:
                    _type = m[2].type.name if m[2] is not None else "None"
                    print("   ","       ", _type, m[0][1])
                print("   ","    メソッド:", len(p.methods))
                for m in p.methods:
                    args = None
                    return_type = None
                    obj = m[2]
                    if obj is not None:
                        return_type = obj.return_type.name if obj.return_type is not None else "(Void)"
                        args = "["+", ".join([i.type.name for i in obj.parameters])+"]"
                    print("   ","       ", m[0][1], m[1], args, "->", return_type)
                print("   ","    定義されたコンストラクタ:", len(p.constructors))
                for c in p.constructors:
                    print("   ","       ", c[:-1], [i.type.name for i in c[-1].parameters])

class Call():
    def __init__(self, project):
        self.project = project
        self.AllProducts = [i.name for i in project.products]
        self.AllTestHelpers = [i.name for i in project.testhelpers]

        self.pool = []

        self.products = []
        self.testhelpers = []
        self.unknown = Class("Unknown")

    #query = [Product/TestHelper/Unknown, member/method/constructor, [cname, name, nargs], obj]
    def addClass(self, cname):
        if cname in self.AllProducts:
            if cname not in [i.name for i in self.products]:
                self.products.append(Class(cname))
        elif cname in self.AllTestHelpers:
            if cname not in [i.name for i in self.testhelpers]:
                self.testhelpers.append(Class(cname))

    def append(self, _type, query, result, obj):
        cname, name, nargs = query

        if _type not in ["members", "methods", "constructors"]:
            return

        if cname is None:
            cname = "(Unknwon)"

        ID = _type+"/"+cname+"/"+name+"/"+str(nargs)
        if ID in self.pool:
            return
        self.pool.append(ID)

        self.addClass(cname)

        if cname in self.AllProducts:
            for c in self.products:
                if c.name == cname:
                    eval("c."+_type).append([query, result, obj])
                    break
        elif cname in self.AllTestHelpers:
            target_list = self.testhelpers
            for c in self.testhelpers:
                if c.name == cname:
                    eval("c."+_type).append([query, result, obj])
                    break
        else:
            eval("self.unknown."+_type).append([query, result, obj])

#プロジェクトパス -> プロダクトコードの[クラスobj, [メソッドobj], [コンストラクタobj]]
#プロジェクトパス -> [クラスobj, [テストメソッドobj], []]

#プロジェクトパス -> テスト補助メソッドの[クラスobj, [メソッドobj], [コンストラクタobj]]
#継承を考慮した完全版リストへの拡張

#SearchBox(母集団, クラス名, メソッド名, 引数数) -> [該当数, [メソッドobj]]









"""ProductMethodsOfTo = getProductMethods(To)
print("移植先プロジェクトにおけるプロダクトコード")
print("    クラス数:", len(ProductMethodsOfTo))
print("    メソッド数:", sum([len(i[1]) for i in ProductMethodsOfTo]))
TP = extended_ProductMethodsOfTo = expandExtends(list(ProductMethodsOfTo))
print("    メソッド数（継承統合後）:", sum([len(i[1]) for i in extended_ProductMethodsOfTo]))
print("    コンストラクタ数:", sum([len(i[2]) for i in ProductMethodsOfTo]))

ProductMethodsOfFrom = getProductMethods(From)
print("移植元プロジェクトにおけるプロダクトコード")
print("    クラス数:", len(ProductMethodsOfFrom))
print("    メソッド数:", sum([len(i[1]) for i in ProductMethodsOfFrom]))
FP = extended_ProductMethodsOfFrom = expandExtends(list(ProductMethodsOfFrom))
print("    メソッド数（継承統合後）:", sum([len(i[1]) for i in extended_ProductMethodsOfFrom]))
print("    コンストラクタ数:", sum([len(i[2]) for i in ProductMethodsOfFrom]))

FTH = TestHelperMethods = getTestHelperMethods(From)
print("移植元プロジェクトにおけるテスト補助コード")
print("    クラス数:", len(TestHelperMethods))
print("    メソッド数:", sum([len(i[1]) for i in TestHelperMethods]))
extended_TestHelperMethods = expandExtends(list(TestHelperMethods))
print("    メソッド数（継承統合後）:", sum([len(i[1]) for i in extended_TestHelperMethods]))
print("    コンストラクタ数:", sum([len(i[2]) for i in TestHelperMethods]))

TestMethods = getTestMethods(From)
print("移植元プロジェクトにおけるテストコード")
#print("    クラス数:", len(TestMethods))
print("    メソッド数:", len(TestMethods))
"""
#SearchBox(FP, "Book","Book",1)

model_from = Project(From)
TestMethods = model_from.tests

n = random.randint(0, 199)
n=131
print(n)
for t in TestMethods[n:n+1]:
    print(t.c_obj.name, t.name)
    t = model_from.extractCall(t)
    t.print()

    for h in t.call.testhelpers:
        for m in h.methods + h.constructors:
            print(h.name, m[0])
            dummy = TestCase("dummy")
            dummy.m_obj = m[-1]
            dummy.c_obj = model_from.getCobj(h.name)
            _dummy = model_from.extractCall(dummy)
            _dummy.print()
