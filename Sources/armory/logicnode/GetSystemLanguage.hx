package armory.logicnode;

class GetSystemLanguage extends LogicNode {

	public function new(tree: LogicTree) {
		super(tree);
	}

	override function get(from: Int): Dynamic {
		if (from == 0) return kha.System.language;
		return null;
	}
}
