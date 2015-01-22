<?php

$TOKEN_TYPES = array(
	Interpreter::CONSTANT	=> 'constant',
	Interpreter::VARIABLE	=> 'variable',
	Interpreter::STR		=> 'string',
	Interpreter::NUMBER		=> 'number',
	Interpreter::OPERATOR	=> 'operator',
	Interpreter::DELIMITER	=> 'delimiter',
	Interpreter::IDENTIFIER	=> 'identifier',
	Interpreter::KEYWORD	=> 'keyword'
);

/*
	INTERPRETER
*/
abstract class Interpreter{
		
	const EXPRESSION	= 0;
	const CONSTANT		= 1;
	const VARIABLE		= 2;
	const STR			= 3;
	const NUMBER		= 4;
	const OPERATOR		= 5;
	const DELIMITER		= 6;
	const IDENTIFIER	= 7;
	const KEYWORD		= 8;
	
	protected $lexer;
	protected $grammar;
	protected $stack;
	protected $store;
	protected $defs;
	
	static protected function error($line, $char, $err = ''){
		die(sprintf("[ %s : %s ] %s", $line, $char, $err));
	}
	
	public function load($source, $type = self::SOURCE_FILE){
		$this->lexer = new Lexer(new Scanner($source, $type), $this->grammar);
	}
	
	abstract public function exec();
}

/*
	DTKINTERPRETER
*/
class DTKInterpreter extends Interpreter{
	
	const INSTR_BLOCK_ADDRESS	= 0;
	
	// slots in statement
	const LEFT_OPERAND	= 0;
	const TERM_OPERATOR	= 1;
	const RIGHT_OPERAND	= 2;
		
	const SOURCE_FILE	= 0;
	const SOURCE_TEXT	= 1;
	
	const S_EOF			= 0;
	const S_DISABLED	= 1;
	const S_DEFAULT		= 2;
	const S_IF			= 3;
	const S_ELSE		= 4;
	const S_FUNCTION	= 5;
	
	protected $transStates		= array(
		'EOF'	=> array(
			self::S_DISABLED	=> null,	
			self::S_DEFAULT		=> self::S_EOF,	
			self::S_IF			=> self::S_EOF,	
			self::S_ELSE		=> self::S_EOF,	
			self::S_FUNCTION	=> self::S_EOF	
		),
		'if'	=> array(
			self::S_DISABLED	=> null,
			self::S_EOF			=> false,
			self::S_DEFAULT		=> self::S_IF,
			self::S_IF			=> null,
			self::S_ELSE		=> null,
			self::S_FUNCTION	=> null
		),
		'else'	=> array(
			self::S_DISABLED	=> null,
			self::S_EOF			=> false,
			self::S_DEFAULT		=> false,
			self::S_IF			=> self::S_ELSE,
			self::S_ELSE		=> false,
			self::S_FUNCTION	=> null
		),
		'def'	=> array(
			self::S_DISABLED	=> null,
			self::S_EOF			=> false,
			self::S_DEFAULT		=> self::S_FUNCTION,
			self::S_IF			=> false,
			self::S_ELSE		=> false,
			self::S_FUNCTION	=> false
		),
		'end'	=> array(
			self::S_DISABLED	=> null,
			self::S_EOF			=> false,
			self::S_DEFAULT		=> null,
			self::S_IF			=> self::S_DEFAULT,
			self::S_ELSE		=> self::S_DEFAULT,
			self::S_FUNCTION	=> self::S_DEFAULT
		)
	);
	protected $state 				= self::S_DEFAULT;
	protected $instrBlock			= array();
	protected $instrBuffer			= array();
	protected $blockAddressStack	= array();
	protected $instrNext			= 0;
	protected $lastToken			= null;
	
	
	/*
	protected $grammarRules = array(	
		array(self::IDENTIFIER, self::OPERATOR, self::CONSTANT),
		array(self::IDENTIFIER, self::OPERATOR, self::IDENTIFIER),
		array(self::IDENTIFIER, self::OPERATOR, self::EXPRESSION),
		array(self::KEYWORD, self::EXPRESSION)
	);
	
	protected $grammarTree = array();
	
	protected function buildGrammarTree(&$tree, $rules){
			
		if(!is_array($rules))
			throw new Exception('Array expected.');
				
		$root = array();
		foreach($rules as $rule){
			$pntr =& $root;
			
					
			for($i = 0; $i < strlen($rule->symbol); $i++){		
			
				if(!isset($pntr[$rule->symbol[$i]]))
					$pntr[$rule->symbol[$i]] = array();
			
				$pntr =& $pntr[$rule->symbol[$i]];
			
			}
			
			$pntr[0] = $rule;
		}
			
		$tree = $root;
	}
	*/
			
	public function DTKInterpreter(Language $grammar){
		$grammar->owner		= $this;
		$this->grammar		= $grammar;
		
		//$this->buildGrammarTree($this->grammarTree, $this->grammarRules);
		
	}
	
	public function passthrough(){
		$this->state = self::S_DISABLED;
		?>
		<table border='1'>
			<tr><th>LINE</th><th>CHAR</th><th>TOKEN</th><th>TYPE</th></tr>
			<?php while($token = $this->nextToken()) echo $token; ?>
		</table><?php
		$this->lexer->reset();
		$this->state = self::S_DEFAULT;
	}
		
	public function exec(){
		
		// COMPILE
		$this->compile();
		$this->state		= self::S_DEFAULT;
		$this->instrNext 	= 0;
		$halt				= false;
					
		// EXECUTE
		while(isset($this->instrBlock[$this->instrNext]) && !$halt){
			$this->evaluate($this->instrBlock[$this->instrNext]);
			$this->instrNext++;
		}
		
		return true;			
	}
	
	public function setNextInstr($n){
		$this->instrNext = $n;
	}
	
	protected function stateMachine($input){
		
		if(is_bool($input) && !$input){
			$this->state = $this->transStates['EOF'][$this->state];
			return false;
		}
		
		if($input instanceof Token)
			$input = $input->symbol;
			
		if(isset($this->transStates[$input]))		
			if($transition = $this->transStates[$input][$this->state])
				if(function_exists($transition))
					$this->state = $transition();
				elseif(method_exists($this, $transition))
					$this->state = $this->$transition();
				else
					$this->state = $transition;
					
		if($this->state === false)
			throw new Exception('Unexpected invalid state.');				
			
		return $this->state;
	}
	
	protected function nextToken(){
		$token = $this->lexer->nextToken();
		$this->lastToken = $token;
		$this->stateMachine($token);
		return $token;
	}
	
	protected function nextStatement(){
		$stat = array();
		while(($token = $this->nextToken()) && ($this->state != self::S_EOF) && ($token->symbol != ';') && ($token->symbol != ':'))
			$stat[] = $token;
		return (count($stat) > 0) ? $stat : false;
	}
	
	protected function compile(){
		
		$this->state = self::S_DEFAULT;
		 
		while($this->state != self::S_EOF)	
			if($statement = $this->nextStatement())
				$this->instrBlock[] = $this->parse($statement);
		
		return true;
	}
	
	private function readBlock(&$code, $delimiter, $includeDelimiters = false){	
			
		if(!is_string($delimiter) && !is_array($delimiter))
			throw new Exception('Invalid delimiter argument');
			
		$delimiter	= (is_string($delimiter)) ? str_split($delimiter) : $delimiter;
		$block		= array();
		$nesting	= (empty($delimiter[0])) ? 1 : 0;
		
		for($i = 0; $i < count($code); $i++){
			if($code[$i]->symbol == $delimiter[0])
				$nesting++;
			elseif($code[$i]->symbol == $delimiter[1])
				$nesting--;	
			
			if($nesting < 0)
				self::error($code[$i]->line, $code[$i]->char, sprintf("Unpaired right delimiter '%s'", $code[$i]->symbol));
			elseif(($nesting > 0) && (count($block) == 0))
				$block[0] = $i;
			elseif(($nesting == 0) && (count($block) > 0) && ($i > 0)){
				$block[1] = $i;
				break;
			}	
		}
				
		if(count($block) == 0)
			return false;
							
		if((!isset($block[0]) && !empty($delimiter[0])) || (!isset($block[1]) && !empty($delimiter[1])))
			throw new Exception('Unexpexted block delimiter error');
								
		$block = array_splice($code, $block[0], ($block[1] + 1) - $block[0]);
		
		if($includeDelimiters)
			return $block;
		else			
			return array_slice($block, empty($delimiter[0]) ? 0 : 1, count($block) - ((empty($delimiter[0]) || empty($delimiter[1])) ? 1 : 2));
	}
	
	protected function handleConstant($node, &$statement, &$tree){
	
		switch(count($tree)):
			case(self::LEFT_OPERAND):
				$tree[self::LEFT_OPERAND] = $node->symbol;
				break;
			case(self::RIGHT_OPERAND):
				$tree[self::RIGHT_OPERAND] = $this->parse($statement, array($node->symbol));	
				break;
			default:
				self::error($node->line, $node->char, sprintf("Misplaced CONSTANT '%s'", $node->symbol));
				break;
		endswitch;
	}
	
	protected function handleIdentifier($node, &$statement, &$tree){
	
		if(!isset($this->store[$node->symbol]))
			$this->store[$node->symbol] = null;	
										
		switch(count($tree)):
			case(self::LEFT_OPERAND):
				if(isset($this->defs[$node->symbol])):
					$this->handleFunctionCall($node, $statement, $tree);
				else:
					$tree[self::LEFT_OPERAND] = new Variable($node, $this->store[$node->symbol]);
				endif;
				break;
			case(self::RIGHT_OPERAND):
				$tree[self::RIGHT_OPERAND] = $this->parse($statement, array(new Variable($node, $this->store[$node->symbol])));	//	Symbol is stored at the left (index 0)
				break;
			default:
				self::error($node->line, $node->char, sprintf("Misplaced IDENTIFIER '%s'", $node->symbol));
				break;
		endswitch;
	}
	
	protected function handleFunctionCall($node, &$statement, &$tree){
		$tree[self::LEFT_OPERAND] = new FunctionCall($node, $this->defs[$node->symbol]->code, $this->readBlock($statement, '()'));
		$tree[self::TERM_OPERATOR]	= null;
		$tree[self::RIGHT_OPERAND]	= null;
	}
	
	protected function handleOperator($node, &$statement, &$tree){
		switch(count($tree)):
			case(self::TERM_OPERATOR):
				$tree[self::TERM_OPERATOR] = $node->symbol;
				break;
			default:
				self::error($node->line, $node->char, sprintf("Misplaced '%s' operator", $node->symbol));
				break;
		endswitch;
	}
	
	protected function handleKeyword($node, &$statement, &$tree){
		
		$term = count($tree);
		
		switch($node->symbol):			
			case('true'):
			case('false'):
				$tree[$term] = $node->symbol;
				break;
			
			case('prnt'):
						
				$tree[$term] = new Keyword($node, $this->parse($statement));		
				
				//for($i = ($term + 1); $i < 3; $i++)
				//	$tree[$i] = null;
							
				break;
			case('repeat'):
				
				if(!($times	= $this->readBlock($statement, '()')))
					self::error($node->line, $node->char, sprintf("Missing times block."));
				
				$this->blockAddressStack[] = array(
					'instr'		=> 'repeat',		
					'address'	=> count($this->instrBlock), 
					'times'		=> $this->parse($times)
				);
			
				break;
				
			case('def'):
				
				$this->blockAddressStack[] = array(
					'instr'	=> 'def'
				);
			
				$identifier = array_shift($statement);
				
				$arguments = $this->readBlock($statement, '()');
				
				if(isset($this->defs[$identifier->symbol]))
					self::error($node->line, $node->char, sprintf("%s already defined", $node->symbol));
			
				$code = array();
				
				while(($statement = $this->nextStatement()) && $statement[0]->symbol != 'end')
					$code[] = $this->parse($statement);
									
				$this->defs[$identifier->symbol] = new FunctionDefinition($node, $arguments, $code);
				
								
				break;
					
			case('if'):
					
				if(!($condition	= $this->readBlock($statement, '()')))
					self::error($node->line, $node->char, sprintf("Missing condition block."));

				$tree[self::LEFT_OPERAND]	= new ConditionalBlock($node, $this->parse($condition), count($this->instrBlock));
				$tree[self::TERM_OPERATOR]	= null;
				$tree[self::RIGHT_OPERAND]	= null;	
							
				$this->blockAddressStack[] = array(
					'instr'			=> 'if',
					'begin'			=> count($this->instrBlock), 
					'falseBlock'	=> null
				);
											
				break;
				
			case('else'):
				
				$tree[self::LEFT_OPERAND]	= new UnconditionalJump();
				$tree[self::TERM_OPERATOR]	= null;
				$tree[self::RIGHT_OPERAND]	= null;	
				$this->blockAddressStack[count($this->blockAddressStack) - 1]['falseBlock'] = count($this->instrBlock);
				break;
				
			case('end'):
			
				$block = array_pop($this->blockAddressStack);	
				
				switch($block['instr']):
					
					case('if'):
						if(isset($block['falseBlock']) && !is_null($block['falseBlock'])){
							$this->instrBlock[$block['begin']][self::LEFT_OPERAND]->falseBlock = $block['falseBlock'];
							$trueJumpAddress = ($this->instrBlock[$block['begin']][self::LEFT_OPERAND]->falseBlock);
							$this->instrBlock[$trueJumpAddress][self::LEFT_OPERAND]->address = count($this->instrBlock);
						} else
							$this->instrBlock[$block['begin']][self::LEFT_OPERAND]->falseBlock = count($this->instrBlock);
						break;
					case('repeat'):
						$tree[self::LEFT_OPERAND]	= new Loop($block['address'], $block['times']);
						$tree[self::TERM_OPERATOR]	= null;
						$tree[self::RIGHT_OPERAND]	= null;	
						break;
					case('def'):
						break;
					default:
						throw new Exception("Unknown language construct '{$block['instr']}'");
						break;
					
				endswitch;
		
				break;	
		
			default:
				throw new Exception('Misplaced KEYWORD: '.$node->symbol);
				break;
				
		endswitch;
	}
	
	protected function handleDelimiter($node, &$statement, &$tree){
		
		$term = count($tree);
	
		switch($node->symbol):
			case('('):
				array_unshift($statement, $node);								
				$expression = $this->readBlock($statement, '()');	
				$tree[$term] = $this->parse( $statement, array( $this->parse( $expression ) ) );									
				break;
			case('}'):
			case(')'):
				die('Unpaired '.$node->symbol);
				break;
			default:
				die('Unexpected delimiter '.$node->symbol);
				break;
		endswitch;
	}
		
	protected function parse(&$statement, $tree = array()){
	
		while(count($statement) > 0){
		
			$node	= array_shift($statement);
			$term	= count($tree);
			$type	= $node->type;
						
			if($term > self::RIGHT_OPERAND)
				return;
				
			//if($term == self::TERM_OPERATOR && $type != self::OPERATOR)
			//	self::error($node->line, $node->char, sprintf("operator expected. Reading '%s'", $node->symbol));
									
			switch($type):
				case(self::IDENTIFIER):
					switch($term):
						case(self::LEFT_OPERAND):
						case(self::TERM_OPERATOR):
						case(self::RIGHT_OPERAND):
							$this->handleIdentifier($node, $statement, $tree);	
							break;
					endswitch;		
					break;
				case(self::KEYWORD):
					switch($term):
						case(self::LEFT_OPERAND):
						case(self::TERM_OPERATOR):
						case(self::RIGHT_OPERAND):
							$this->handleKeyword($node, $statement, $tree);
							break;
					endswitch;
					break;
				case(self::STR):
				case(self::CONSTANT):
					switch($term):
						case(self::LEFT_OPERAND):
						case(self::TERM_OPERATOR):
						case(self::RIGHT_OPERAND):
							$this->handleConstant($node, $statement, $tree);	
							break;
					endswitch;	
					break;
				case(self::OPERATOR):
					switch($term):
						case(self::LEFT_OPERAND):
						case(self::TERM_OPERATOR):
						case(self::RIGHT_OPERAND):
							$this->handleOperator($node, $statement, $tree);
							break;
					endswitch;
					break;
				case(self::DELIMITER):
					switch($term):
						case(self::LEFT_OPERAND):
						case(self::TERM_OPERATOR):
						case(self::RIGHT_OPERAND):
							$this->handleDelimiter($node, $statement, $tree);
							break;
					endswitch;
					break;
				default:
					die('Unexpected '.$node->symbol);
					break;
			endswitch;
		}
		
		return $tree;
	}
	
	protected function evaluate($tree){
			
		if(empty($tree))
			return null;
				
		if(!empty($tree[self::RIGHT_OPERAND]))
			if(is_array($tree[self::RIGHT_OPERAND]))
				$right = $this->evaluate($tree[self::RIGHT_OPERAND]);
			else
				$right = $tree[self::RIGHT_OPERAND];
		else $right = null;
		
		if(is_array($tree[self::LEFT_OPERAND]))
			$left = $this->evaluate($tree[self::LEFT_OPERAND]);
		else
			$left = $tree[self::LEFT_OPERAND];

		// handle internal instructions
		if($left instanceof InternalInstruction):
			
			if($left instanceof UnconditionalJump){
				if((isset($left->address) && !is_null($left->address))){
					$this->instrNext = $left->address;
				}
			} elseif($left instanceof Loop){
				
				if(is_null($left->count))
					$left->count = $this->evaluate($left->times);
				elseif($left->count > 1)
					$left->count--;
				elseif($left->count < 1)
					$left->count++;
					
				if($left->count != 1)
					$this->setNextInstr($left->address);
			
			}
			
			return;
		endif;
		// end of block
		
		// hande language constructs					
		if($left instanceof Keyword):
			$func = $this->grammar->bindings[$left->symbol];
			if($left instanceof ConditionalBlock)
				$left = $this->grammar->$func($left, $this->evaluate($left->condition));
			else
				$left = $this->grammar->$func($this->evaluate($left->argument));
		endif;
		// end of block
		
		if($left instanceof FunctionCall):
			var_dump($left->address);
			die('Ack!');
		endif;
						
		if(!empty($tree[self::TERM_OPERATOR])){
				
			if(!isset($this->grammar->bindings[$tree[self::TERM_OPERATOR]]))
				throw new Exception('Undefined operator: '.$tree[self::TERM_OPERATOR]);
				
			$func = $this->grammar->bindings[$tree[self::TERM_OPERATOR]];
				
			return $this->grammar->$func($left, $right, $this->store);
		}			
			
		if($left instanceof Variable)
			return $this->store[$left->symbol];
	
		return $left;
	}
}
		
/*
	DOUBLETALK
*/
class Doubletalk extends Language{

	public $bindings = array(
		//','		=> 'nlist',
		'+'			=> 'plus',
		'-'			=> 'minus',
		'*'			=> 'multiply',
		'/'			=> 'divide',
		'='			=> 'assign',
		'=='		=> 'equal',
		'!='		=> 'unequal',
		'prnt'		=> 'prnt',
		'if'		=> 'conditional'
	);

	public function prnt($arg){
		echo $arg;
	} 
		
	private function value($var){		
		return ($var instanceof Variable) ? $var->address : $var;
	}
	
	public function nlist($left, $right){
		
		if(is_array($left) && is_array($right))
			return array_merge($left, $right);
		
		if(is_array($left))
			return $left[] = $right;
			
		if(is_array($right))
			return $right[] = $left;
			
		return array($left, $right);
	}
	
	public function equal($left, $right){
		return $this->value($left) == $this->value($right);
	}
	
	public function unequal($left, $right){
		return $this->value($left) != $this->value($right);
	}
	
	public function plus($left, $right){
		return ($this->value($left) * 1) + ($this->value($right) * 1);
	}
	
	public function minus($left, $right){
		$left	= ($this->value($left) * 1);
		$right	= ($this->value($right) * 1);	
		return  $left - $right;
	}
	
	public function multiply($left, $right){
		$left	= ($this->value($left) * 1);
		$right	= ($this->value($right) * 1);
		return  $left * $right;
	}
	
	public function divide($left, $right){
		$left	= ($this->value($left) * 1);
		$right	= ($this->value($right) * 1);	
		return  $left / $right;
	}
	
	public function assign(Variable $left, $right){
		return ($left->address = $this->value($right));		
	}
	
	public function conditional(ConditionalBlock $ifBlock, $condition){
		if($condition === false)
			if(isset($ifBlock->falseBlock) && !is_null($ifBlock->falseBlock))
				$this->owner->setNextInstr($ifBlock->falseBlock);
	}
	
}

/*
	DOUBLETALK 
*/
		
$operators = array(
	new Token('+'),
	new Token('-'),
	new Token('/'),
	new Token('*'),
	new Token('>'),
	new Token('<'),
	new Token('!'),
	new Token('|'),
	new Token('&'),
	new Token('='),
	new Token('=='),
	new Token('!='),
	new Token('+='),
	new Token('-='),
	new Token('*='),
	new Token('/='),
	new Token('>='),
	new Token('<='),
	new Token('++'),
	new Token('--'),
	new Token('->'),
	new Token('<-'),
	new Token('::=')
);
	
$delimiters = array(
	new Token('('),
	new Token(')'),
	new Token('{'),
	new Token('}'),
	new Token('['),
	new Token(']'),
	new Token(':'),
	new Token(';'),
	new Token('.'),
	new Token(',')
);

$keywords = array(
	new Token('[HEAD]'),
	new Token('[PROC]'),
	new Token('[INSTR]'),
	new Token('[END]'),
	new Token('prnt'),
	new Token('true'),
	new Token('false'),
	new Token('if'),
	new Token('else'),
	new Token('end'),
	new Token('repeat'),
	new Token('until'),
	new Token('def')
);
	
$DTKlang = new Doubletalk();
$DTKlang->setRulesNumbers(
	new Token("/^[0-9.]*$/")
);
$DTKlang->setRulesIdentifiers(
	new Token("/^[A-Za-z_]+[0-9_]*$/")
);
$DTKlang->setRulesComments(
	new Token('//'), 
	new Token('/*'), 
	new Token('*/') 
);
$DTKlang->setRulesStringLiterals(
	new Token("'"),
	new Token('"')
);
$DTKlang->setOperators($operators);
$DTKlang->setDelimiters($delimiters);
$DTKlang->setKeywords($keywords);
?>
